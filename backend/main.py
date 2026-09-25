import datetime, secrets, uuid, time, threading, re, io, csv, asyncio
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from urllib.parse import urlparse
from contextlib import asynccontextmanager
from types import SimpleNamespace
from fastapi import FastAPI, Request, Response, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from .db import *
from .security import hash_password, verify_password, digest
from .rag import answer, index_document, embed
from .text_processing import inspect_pdf, PDFValidationError, MAX_PDF_BYTES


@asynccontextmanager
async def lifespan(app):
    initialize()
    # Load the local embedding model before accepting saves or chat requests.
    await asyncio.to_thread(embed, ["เตรียมระบบค้นหาข้อมูล"])
    yield


app = FastAPI(title="SCI Chatbot", lifespan=lifespan)
rates = defaultdict(list)
rate_lock = threading.Lock()
allowed_origins = {
    "http://localhost:3100", "http://127.0.0.1:3100",
    "http://localhost:8010", "http://127.0.0.1:8010",
}
allowed_origins.update(
    value.strip() for value in os.environ.get("SCI_ALLOWED_ORIGINS", "").split(",")
    if value.strip()
)


def limit(key, n, seconds):
    with rate_lock:
        t = time.time()
        rates[key] = [x for x in rates[key] if t - x < seconds]
        if len(rates[key]) >= n:
            raise HTTPException(429, "กรุณารอสักครู่แล้วลองใหม่")
        rates[key].append(t)


def db_session():
    with Session() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise


@app.middleware("http")
async def guards(req, call_next):
    if req.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = req.headers.get("origin")
        if origin and origin not in allowed_origins:
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "ไม่อนุญาตคำขอจากเว็บไซต์อื่น"}, 403)
    response = await call_next(req)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


def current_user(req: Request, db=Depends(db_session)):
    token = req.cookies.get("sci_auth", "")
    auth = db.get(Auth, digest(token))
    if not auth or auth.expires < now():
        raise HTTPException(401, "กรุณาเข้าสู่ระบบ")
    u = db.get(User, auth.user_id)
    if not u or not u.active:
        raise HTTPException(401, "บัญชีไม่พร้อมใช้งาน")
    return u


def owner(req):
    token = req.cookies.get("sci_guest", "")
    if not token:
        raise HTTPException(401, "กรุณาเปิดหน้าสนทนาใหม่")
    return digest(token)


def serialize(row, db=None):
    d = {
        c.key: (float(getattr(row, c.key)) if isinstance(getattr(row, c.key), Decimal) else getattr(row, c.key))
        for c in row.__mapper__.column_attrs
        if c.key not in ("password", "owner", "embedding")
    }
    if db is not None and isinstance(row, User):
        d["major_ids"] = list(
            db.scalars(select(MajorUser.major_id).where(MajorUser.user_id == row.id))
        )
    if db is not None and row.__tablename__ == "curricula":
        d["career_ids"] = list(
            db.scalars(
                select(CurriculumCareer.career_id).where(
                    CurriculumCareer.curriculum_id == row.id
                )
            )
        )
    return d


def majors(db, u):
    return list(db.scalars(select(MajorUser.major_id).where(MajorUser.user_id == u.id)))


def authorize(entity, u):
    if entity not in MODELS:
        raise HTTPException(404, "ไม่พบรายการ")
    allowed = {"admin": {"users", "majors", "general", "news", "intents"}, "staff": {"curricula", "careers"}}
    if entity not in allowed.get(u.role, set()):
        raise HTTPException(403, "ไม่มีสิทธิ์จัดการข้อมูลนี้")


def scoped(stmt, entity, db, u):
    if u.role == "staff":
        if entity == "curricula":
            stmt = stmt.where(MODELS[entity].major_id.in_(majors(db, u)))
        elif entity == "careers":
            stmt = stmt.where(MODELS[entity].user_id == u.id)
    return stmt


def getrow(entity, id, db, u):
    authorize(entity, u)
    row = db.scalar(
        scoped(select(MODELS[entity]).where(MODELS[entity].id == id), entity, db, u)
    )
    if not row:
        raise HTTPException(404, "ไม่พบรายการ")
    return row


def valid_url(v):
    if re.search(r"[\s\\\x00-\x1f]", v):
        return False
    if v.startswith("/api/uploads/"):
        return bool(re.fullmatch(r"/api/uploads/[a-f0-9]{32}\.(pdf|png|jpe?g)", v))
    try:
        p = urlparse(v)
        _ = p.port
        return p.scheme in ("http", "https") and bool(p.hostname) and not (p.username or p.password)
    except ValueError:
        return False


def validate_email(value):
    if value and not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", value):
        raise HTTPException(422, "รูปแบบอีเมลไม่ถูกต้อง")


def validate_attachment(key, value):
    if not value:
        return
    suffix = Path(urlparse(value).path).suffix.lower()
    allowed = {'.pdf'} if key == 'file_url' else {'.png', '.jpg', '.jpeg'}
    # Remote links are references, not an implicit server-side download. Known
    # incompatible types are rejected; extensionless download URLs remain valid.
    if suffix in {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.exe'} and suffix not in allowed:
        raise HTTPException(422, "ช่องหลักสูตรรองรับ PDF และช่องรูปภาพรองรับ PNG/JPG เท่านั้น")
    if value.startswith('/api/uploads/'):
        path = ROOT / 'data/uploads' / value.rsplit('/', 1)[-1]
        if suffix not in allowed or not path.is_file():
            raise HTTPException(422, "ไม่พบไฟล์แนบหรือชนิดไฟล์ไม่ตรงกับช่องที่เลือก")


def clean(entity, payload, db, u, row=None):
    columns = {c.key: c.columns[0] for c in MODELS[entity].__mapper__.column_attrs}
    fields = set(columns) - {
        "id",
        "created_at",
        "updated_at",
        "user_id",
        "password",
        "views_count",
    }
    data = {k: v for k, v in payload.items() if k in fields}
    data = {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}
    for k, v in data.items():
        column = columns[k]
        if v is not None and isinstance(column.type, (String, Text)) and not isinstance(v, str):
            raise HTTPException(422, "รูปแบบข้อความไม่ถูกต้อง")
        if isinstance(column.type, Boolean) and not isinstance(v, bool):
            raise HTTPException(422, "รูปแบบสถานะไม่ถูกต้อง")
        if isinstance(v, str):
            if len(v) > (10 if isinstance(column.type, UserRole) else (getattr(column.type, 'length', None) or 25000)):
                raise HTTPException(422, "ข้อความยาวเกินไป")
            if (
                (
                    k.endswith("_url")
                    or k in ("facebook_page", "website_url", "cover_image")
                )
                and v
                and not valid_url(v)
            ):
                raise HTTPException(422, "ลิงก์ต้องขึ้นต้นด้วย http หรือ https")
            if k == 'email':
                validate_email(v)
            if k in ('file_url', 'image_url', 'cover_image'):
                validate_attachment(k, v)
    if entity == "users":
        if data.get("role") not in ("admin", "staff"):
            raise HTTPException(422, "บทบาทไม่ถูกต้อง")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,255}", data.get("username", "")):
            raise HTTPException(
                422, "ชื่อผู้ใช้ต้องเป็นอักษรอังกฤษหรือตัวเลขอย่างน้อย 3 ตัว"
            )
        password = payload.get("password", "")
        if not isinstance(password, str) or len(password) > 200:
            raise HTTPException(422, "รูปแบบรหัสผ่านไม่ถูกต้อง")
        if password:
            if len(password) < 10:
                raise HTTPException(422, "รหัสผ่านต้องมีอย่างน้อย 10 ตัวอักษร")
            data["password"] = hash_password(password)
        elif row is None:
            raise HTTPException(422, "กรุณาระบุรหัสผ่าน")
        if (
            row
            and row.id == u.id
            and (data.get("role") != "admin" or data.get("active") is False)
        ):
            raise HTTPException(422, "ไม่สามารถลดสิทธิ์หรือปิดบัญชีของตนเอง")
    if entity == "curricula":
        mid = data.get("major_id")
        if type(mid) is not int or mid <= 0:
            raise HTTPException(422, "กรุณาเลือกสาขาวิชา")
        if not db.get(MODELS["majors"], mid):
            raise HTTPException(422, "กรุณาเลือกสาขาวิชา")
        if u.role == "staff" and mid not in majors(db, u):
            raise HTTPException(403, "ไม่มีสิทธิ์ในสาขาวิชานี้")
    for k in ("total_credits", "curriculum_year"):
        if data.get(k) is not None and (type(data[k]) is not int or not 0 <= data[k] <= 2147483647):
            raise HTTPException(422, "ปีหลักสูตรและหน่วยกิตต้องเป็นจำนวนเต็มที่ไม่ติดลบ")
    for k in ("tuition_fee", "salary_start"):
        if data.get(k) is not None:
            try:
                if isinstance(data[k], bool):
                    raise ValueError()
                amount = Decimal(str(data[k]))
                if not amount.is_finite() or not 0 <= amount <= Decimal('99999999.99') or amount != amount.quantize(Decimal('0.01')):
                    raise ValueError()
                data[k] = amount
            except (InvalidOperation, ValueError):
                raise HTTPException(422, "จำนวนเงินต้องไม่ติดลบและมีทศนิยมไม่เกิน 2 ตำแหน่ง")
    required = {
        "majors": "major_name_th",
        "general": "topic",
        "news": "title",
        "curricula": "degree_name",
        "careers": "job_title",
        "intents": "intent_name",
        "users": "fullname",
    }[entity]
    if not str(data.get(required, "")).strip():
        raise HTTPException(422, "กรุณากรอกข้อมูลที่จำเป็น")
    if data.get(required) is None:
        raise HTTPException(422, "กรุณากรอกข้อมูลที่จำเป็น")
    extra_required = {'general': 'description', 'news': 'content'}.get(entity)
    if extra_required and not (data.get(extra_required) or '').strip():
        raise HTTPException(422, "กรุณากรอกข้อมูลที่จำเป็น")
    if entity == "intents":
        if data.get("action_type") not in ("rule_based", "rag"):
            raise HTTPException(422, "รูปแบบคำตอบไม่ถูกต้อง")
        if data.get("action_type") == "rule_based" and not data.get("static_response"):
            raise HTTPException(422, "กรุณาระบุคำตอบ")
    if entity == "careers" and data.get("work_sector") not in ("g", "p", "o", "s", "n"):
        raise HTTPException(422, "ประเภทหน่วยงานไม่ถูกต้อง")
    return data


def relations(entity, row, payload, db, u):
    for key in ('major_ids', 'career_ids'):
        if key in payload and (not isinstance(payload[key], list) or any(type(i) is not int or i <= 0 for i in payload[key])):
            raise HTTPException(422, "รายการที่เลือกไม่ถูกต้อง")
    if entity == "users":
        ids = payload.get("major_ids", [])
        if any(not db.get(MODELS["majors"], int(i)) for i in ids):
            raise HTTPException(422, "ไม่พบสาขาวิชา")
        db.execute(delete(MajorUser).where(MajorUser.user_id == row.id))
        for i in set(ids):
            db.add(MajorUser(user_id=row.id, major_id=int(i)))
    if entity == "curricula":
        ids = payload.get("career_ids", [])
        for i in ids:
            getrow("careers", int(i), db, u)
        db.execute(
            delete(CurriculumCareer).where(CurriculumCareer.curriculum_id == row.id)
        )
        for i in set(ids):
            db.add(CurriculumCareer(curriculum_id=row.id, career_id=int(i)))


def sync_doc(entity, row, db):
    warnings = []
    if entity in ("users", "intents"):
        return warnings
    doc = db.scalar(
        select(Document).where(
            Document.record_type == entity, Document.record_id == row.id
        )
    )
    content = "\n".join(
        f"{k}: {v}"
        for k, v in serialize(row).items()
        if v and k not in ("id", "created_at", "updated_at", "user_id")
    )
    title = next(
        (
            getattr(row, k)
            for k in ["topic", "title", "major_name_th", "degree_name", "job_title"]
            if hasattr(row, k)
        ),
        "ข้อมูลคณะ",
    )
    if doc is None:
        doc = Document(
            url=f"/records/{entity}/{row.id}", record_type=entity, record_id=row.id
        )
        db.add(doc)
    if entity == "curricula" and (row.file_url or "").startswith("/api/uploads/"):
        name = row.file_url.rsplit("/", 1)[-1]
        if re.fullmatch(r"[a-f0-9]{32}\.pdf", name):
            try:
                extraction = inspect_pdf(ROOT / "data/uploads" / name)
                content += "\n" + extraction.text
                warnings.extend(extraction.warnings)
            except PDFValidationError as exc:
                raise HTTPException(422, str(exc))
            except Exception:
                raise HTTPException(422, "อ่านไฟล์ PDF ไม่ได้ กรุณาตรวจสอบไฟล์")
    doc.title = title
    doc.content = content
    doc.method = "staff"
    doc.retrieved_at = now().isoformat()
    index_document(db, doc)
    return warnings


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "ข้อมูลซ้ำหรือมีรายการอื่นใช้งานอยู่")


@app.get("/api/health")
def health(db=Depends(db_session)):
    return {
        "application": "sci-chatbot-capstone",
        "status": "ok",
        "database": db.scalar(select(func.count(User.id))) >= 0,
        "documents": db.scalar(select(func.count(Document.id))),
        "chunks": db.scalar(select(func.count(Chunk.id))),
    }


class Login(BaseModel):
    username: str = Field(max_length=255)
    password: str = Field(max_length=200)


@app.post("/api/auth/login")
def login(body: Login, req: Request, res: Response, db=Depends(db_session)):
    limit("login:" + req.client.host, 8, 60)
    u = db.scalar(select(User).where(User.username == body.username))
    if not u or not u.active or not verify_password(body.password, u.password):
        raise HTTPException(401, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    token = secrets.token_urlsafe(32)
    db.add(
        Auth(
            token=digest(token),
            user_id=u.id,
            expires=now() + datetime.timedelta(hours=8),
        )
    )
    db.commit()
    res.set_cookie("sci_auth", token, httponly=True, samesite="strict", max_age=28800)
    return serialize(u, db)


@app.post("/api/auth/logout")
def logout(req: Request, res: Response, db=Depends(db_session)):
    db.execute(
        delete(Auth).where(Auth.token == digest(req.cookies.get("sci_auth", "")))
    )
    db.commit()
    res.delete_cookie("sci_auth")
    return {"ok": True}


@app.get("/api/auth/me")
def me(u=Depends(current_user), db=Depends(db_session)):
    return serialize(u, db)


@app.patch("/api/profile")
def profile(body: dict, u=Depends(current_user), db=Depends(db_session)):
    if u.role != "staff":
        raise HTTPException(403, "ไม่มีสิทธิ์จัดการข้อมูลนี้")
    row = db.get(User, u.id)
    for k in ("fullname", "email", "tel_no"):
        if k in body:
            value = body[k]
            maximum = 20 if k == 'tel_no' else 255
            if not isinstance(value, str) or len(value) > maximum or (k == 'fullname' and not value.strip()):
                raise HTTPException(422, "กรุณาตรวจสอบชื่อ อีเมล และเบอร์โทรศัพท์")
            if k == 'email':
                validate_email(value.strip())
            setattr(row, k, value.strip())
    if body.get("new_password"):
        if not isinstance(body['new_password'], str) or not isinstance(body.get('current_password'), str) or len(body['new_password']) > 200:
            raise HTTPException(422, "รูปแบบรหัสผ่านไม่ถูกต้อง")
        if not verify_password(body.get("current_password", ""), row.password):
            raise HTTPException(422, "รหัสผ่านเดิมไม่ถูกต้อง")
        if len(body["new_password"]) < 10:
            raise HTTPException(422, "รหัสผ่านต้องมีอย่างน้อย 10 ตัวอักษร")
        row.password = hash_password(body["new_password"])
        db.execute(delete(Auth).where(Auth.user_id == u.id))
    commit(db)
    return serialize(row, db)


@app.get("/api/lookups")
def lookups(u=Depends(current_user), db=Depends(db_session)):
    return {
        "majors": [serialize(x) for x in db.scalars(select(MODELS["majors"]))],
        "careers": [
            serialize(x)
            for x in db.scalars(scoped(select(MODELS["careers"]), "careers", db, u))
        ],
    }


@app.get("/api/manage/{entity}")
def listing(entity: str, q: str = "", u=Depends(current_user), db=Depends(db_session)):
    authorize(entity, u)
    rows = db.scalars(
        scoped(select(MODELS[entity]).order_by(MODELS[entity].id.desc()), entity, db, u)
    ).all()
    return [
        serialize(x, db)
        for x in rows
        if not q or q.lower() in str(serialize(x)).lower()
    ]


@app.post("/api/manage/{entity}")
def create(entity: str, body: dict, u=Depends(current_user), db=Depends(db_session)):
    authorize(entity, u)
    data = clean(entity, body, db, u)
    row = MODELS[entity](**data)
    if hasattr(row, "user_id"):
        row.user_id = u.id
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        raise HTTPException(409, "ข้อมูลซ้ำ")
    relations(entity, row, body, db, u)
    warnings = sync_doc(entity, row, db)
    commit(db)
    return {**serialize(row, db), "ingestion_warnings": warnings}


@app.put("/api/manage/{entity}/{id}")
def update(
    entity: str, id: int, body: dict, u=Depends(current_user), db=Depends(db_session)
):
    row = getrow(entity, id, db, u)
    for k, v in clean(entity, body, db, u, row).items():
        setattr(row, k, v)
    if entity in ('news', 'curricula'):
        row.user_id = u.id
    relations(entity, row, body, db, u)
    warnings = sync_doc(entity, row, db)
    commit(db)
    return {**serialize(row, db), "ingestion_warnings": warnings}


@app.delete("/api/manage/{entity}/{id}")
def remove(entity: str, id: int, u=Depends(current_user), db=Depends(db_session)):
    row = getrow(entity, id, db, u)
    if entity == "users" and id == u.id:
        raise HTTPException(422, "ไม่สามารถลบบัญชีของตนเอง")
    db.execute(
        delete(Document).where(Document.record_type == entity, Document.record_id == id)
    )
    db.delete(row)
    commit(db)
    return {"ok": True}


@app.post("/api/uploads")
async def upload(file: UploadFile = File(...), u=Depends(current_user)):
    suffix = Path(file.filename or "").suffix.lower()
    limit = MAX_PDF_BYTES if suffix == '.pdf' else 8 * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, "ไฟล์ PDF ต้องไม่เกิน 32 MB และรูปภาพต้องไม่เกิน 8 MB")
    good = (
        (suffix == ".pdf" and content.startswith(b"%PDF-"))
        or (suffix == ".png" and content.startswith(b"\x89PNG"))
        or (suffix in (".jpg", ".jpeg") and content.startswith(b"\xff\xd8\xff"))
    )
    if not good:
        raise HTTPException(422, "รองรับไฟล์ PDF, PNG และ JPG เท่านั้น")
    try:
        if suffix == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted or not len(reader.pages):
                raise ValueError('Unreadable PDF')
        else:
            from PIL import Image
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != ('PNG' if suffix == '.png' else 'JPEG'):
                        raise ValueError('Wrong image format')
                    image.verify()
    except Exception:
        raise HTTPException(422, "ไฟล์เสียหาย เข้ารหัส หรืออ่านไม่ได้ กรุณาตรวจสอบไฟล์")
    name = secrets.token_hex(16) + suffix
    (ROOT / "data/uploads" / name).write_bytes(content)
    return {"url": "/api/uploads/" + name}


@app.get("/api/uploads/{name}")
def uploaded(name: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.(pdf|png|jpe?g)", name):
        raise HTTPException(404)
    path = ROOT / "data/uploads" / name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(
        path, headers={"Content-Security-Policy": "default-src 'none'; sandbox"}
    )


@app.get("/api/conversations")
def conversations(req: Request, res: Response, db=Depends(db_session)):
    token = req.cookies.get("sci_guest")
    if not token:
        token = secrets.token_urlsafe(32)
        res.set_cookie(
            "sci_guest",
            token,
            httponly=True,
            samesite="strict",
            max_age=60 * 60 * 24 * 30,
        )
    return [
        serialize(x)
        for x in db.scalars(
            select(Conversation)
            .where(Conversation.owner == digest(token))
            .order_by(Conversation.created_at.desc())
        )
    ]


def own_conversation(id, req, db):
    row = db.get(Conversation, id)
    if not row or row.owner != owner(req):
        raise HTTPException(404, "ไม่พบบทสนทนา")
    return row


@app.post("/api/conversations")
def new_conversation(req: Request, db=Depends(db_session)):
    limit("new:" + owner(req), 20, 60)
    row = Conversation(id=str(uuid.uuid4()), owner=owner(req), title="บทสนทนาใหม่")
    db.add(row)
    db.commit()
    return serialize(row)


@app.get("/api/conversations/{id}")
def history(id: str, req: Request, db=Depends(db_session)):
    own_conversation(id, req, db)
    return [
        serialize(x)
        for x in db.scalars(select(Chat).where(Chat.session_id == id).order_by(Chat.id))
    ]


@app.patch("/api/conversations/{id}")
def change_conversation(id: str, body: dict, req: Request, db=Depends(db_session)):
    row = own_conversation(id, req, db)
    if "title" in body:
        if not isinstance(body['title'], str) or not 1 <= len(body['title'].strip()) <= 120:
            raise HTTPException(422, "ชื่อบทสนทนาต้องมี 1–120 ตัวอักษร")
        row.title = body['title'].strip()
    if "rating" in body:
        if type(body["rating"]) is not int or not 1 <= body["rating"] <= 5:
            raise HTTPException(422, "คะแนนต้องอยู่ระหว่าง 1 ถึง 5")
        row.rating = body["rating"]
        row.rated_at = now()
    db.commit()
    return serialize(row)


@app.delete("/api/conversations/{id}")
def delete_conversation(id: str, req: Request, db=Depends(db_session)):
    row = own_conversation(id, req, db)
    db.delete(row)
    db.commit()
    return {"ok": True}


class Question(BaseModel):
    message: str = Field(min_length=1, max_length=1500)


@app.post("/api/conversations/{id}/messages")
def chat(id: str, body: Question, req: Request, db=Depends(db_session)):
    row = own_conversation(id, req, db)
    limit("chat:" + owner(req), 10, 60)
    q = body.message.strip()
    if not q:
        raise HTTPException(422, "กรุณาพิมพ์คำถาม")
    start = time.monotonic()
    # Reconstruct context from this session's questions only. Do not load all
    # response bodies, citations or other sessions to recover the active scope.
    history = [SimpleNamespace(user_query=value) for value in db.scalars(
        select(Chat.user_query).where(Chat.session_id == id).order_by(Chat.id)
    )]
    body, sources, answered, intent, mode = answer(db, q, history)
    item = Chat(
        session_id=id,
        user_query=q,
        bot_response=body,
        is_answered=answered,
        intent_id=intent,
        sources=sources,
        answer_mode=mode,
        response_time_ms=int((time.monotonic() - start) * 1000),
    )
    db.add(item)
    if not history:
        row.title = q[:70]
    db.commit()
    return serialize(item)


@app.patch("/api/messages/{id}/feedback")
def feedback(id: int, body: dict, req: Request, db=Depends(db_session)):
    row = db.get(Chat, id)
    if not row:
        raise HTTPException(404)
    own_conversation(row.session_id, req, db)
    if body.get("is_helpful") is not None and type(body.get("is_helpful")) is not bool:
        raise HTTPException(422)
    row.is_helpful = body.get("is_helpful")
    db.commit()
    return serialize(row)


@app.get("/api/reports/{kind}")
def report(
    kind: str,
    start: str = "",
    end: str = "",
    u=Depends(current_user),
    db=Depends(db_session),
):
    if kind not in ("dashboard", "usage", "satisfaction", "unanswered"):
        raise HTTPException(404)
    if u.role != "admin" and kind in ("dashboard", "usage"):
        raise HTTPException(403, "ไม่มีสิทธิ์ดูสถิติการใช้งาน")
    stmt = select(Chat)
    cs = select(Conversation)
    try:
        if start and end and datetime.date.fromisoformat(start) > datetime.date.fromisoformat(end):
            raise ValueError('Reversed date range')
        if start:
            d = datetime.datetime.fromisoformat(start).replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=7))
            )
            stmt = stmt.where(Chat.timestamp >= d)
            cs = cs.where(Conversation.created_at >= d)
        if end:
            d = datetime.datetime.fromisoformat(end).replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=7))
            ) + datetime.timedelta(days=1)
            stmt = stmt.where(Chat.timestamp < d)
            cs = cs.where(Conversation.created_at < d)
    except ValueError:
        raise HTTPException(422, "วันที่ไม่ถูกต้อง")
    rows = db.scalars(stmt.order_by(Chat.id.desc())).all()
    convs = db.scalars(cs).all()
    ratings = [c.rating for c in convs if c.rating]
    daily = {}
    for x in rows:
        k = (
            x.timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
            .date()
            .isoformat()
        )
        daily[k] = daily.get(k, 0) + 1
    result = {
        "visitors": len(set(c.owner for c in convs)),
        "messages": len(rows),
        "conversations": len(convs),
        "answered": sum(bool(x.is_answered) for x in rows),
        "unanswered": sum(not x.is_answered for x in rows),
        "likes": sum(x.is_helpful is True for x in rows),
        "dislikes": sum(x.is_helpful is False for x in rows),
        "rating_count": len(ratings),
        "rating_average": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "rating_distribution": {str(i): ratings.count(i) for i in range(1, 6)},
        "daily": daily,
        "rows": [
            serialize(x) for x in rows if kind != "unanswered" or not x.is_answered
        ],
        "data_counts": {
            k: db.scalar(select(func.count(v.id)))
            for k, v in MODELS.items()
            if k != "users" or u.role == "admin"
        },
    }
    if u.role == "staff":
        keep = (
            {
                "rows",
                "rating_count",
                "rating_average",
                "rating_distribution",
                "likes",
                "dislikes",
            }
            if kind == "satisfaction"
            else {"rows", "unanswered"}
        )
        return {k: v for k, v in result.items() if k in keep}
    return result


@app.patch("/api/unanswered/{id}")
def resolve(id: int, body: dict, u=Depends(current_user), db=Depends(db_session)):
    if type(body.get('resolved')) is not bool:
        raise HTTPException(422, "สถานะการตรวจสอบไม่ถูกต้อง")
    row = db.get(Chat, id)
    if not row or row.is_answered:
        raise HTTPException(404)
    row.resolved = bool(body.get("resolved"))
    db.commit()
    return {"ok": True}


@app.get("/api/records/{entity}/{id}")
def public_record(entity: str, id: int, db=Depends(db_session)):
    if entity not in ("majors", "curricula", "general", "news", "careers"):
        raise HTTPException(404)
    row = db.get(MODELS[entity], id)
    if not row:
        raise HTTPException(404)
    if entity == 'news':
        # Count successful public detail requests, not admin previews or chat retrievals.
        from sqlalchemy import update as sql_update
        db.execute(sql_update(MODELS['news']).where(MODELS['news'].id == id).values(
            views_count=MODELS['news'].views_count + 1, updated_at=MODELS['news'].updated_at))
        db.commit()
        db.refresh(row)
    return serialize(row)


@app.get("/api/records/overview")
def public_overview(db=Depends(db_session)):
    rows = db.scalars(select(MODELS["majors"]).order_by(MODELS["majors"].id)).all()
    return {
        "title": "ข้อมูลสาขาวิชา",
        "description": "\n".join(
            f"{i+1}. {x.major_name_th}" for i, x in enumerate(rows)
        ),
        "source_url": "https://sci.pcru.ac.th/course",
    }
