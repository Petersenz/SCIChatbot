"""Integration tests against the isolated capstone database; unique fixtures removed after tests."""

from pathlib import Path
import sys, json, uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import Session, MODELS, Chat, Conversation, Auth, User, Document, Chunk
from sqlalchemy import select, delete
import pytest

accounts = json.loads(
    (Path(__file__).resolve().parents[1] / "data/local-accounts.json").read_text(
        encoding="utf-8"
    )
)


@pytest.fixture
def admin():
    with TestClient(app, client=("qa-" + uuid.uuid4().hex, 50000)) as c:
        a = next(x for x in accounts if x["role"] == "admin")
        status = c.post("/api/auth/login", json=a).status_code
        assert status == 200
        yield c


@pytest.fixture
def staff():
    with TestClient(app, client=("qa-" + uuid.uuid4().hex, 50000)) as c:
        a = next(x for x in accounts if x["role"] == "staff")
        status = c.post("/api/auth/login", json=a).status_code
        assert status == 200
        yield c


def test_auth_and_origin():
    with TestClient(app) as c:
        assert c.get("/api/manage/users").status_code == 401
        assert (
            c.post(
                "/api/auth/login", json={"username": "nope", "password": "incorrect"}
            ).status_code
            == 401
        )
        assert (
            c.post(
                "/api/auth/login",
                json=accounts[0],
                headers={"origin": "https://evil.example"},
            ).status_code
            == 403
        )


def test_staff_boundaries(staff):
    for route in [
        "/api/manage/users",
        "/api/manage/intents",
        "/api/manage/general",
        "/api/reports/usage",
        "/api/reports/dashboard",
    ]:
        assert staff.get(route).status_code == 403
    for route in [
        "/api/manage/curricula",
        "/api/manage/careers",
        "/api/reports/satisfaction",
        "/api/reports/unanswered",
    ]:
        assert staff.get(route).status_code == 200
    mids = staff.get("/api/auth/me").json()["major_ids"]
    allm = staff.get("/api/lookups").json()["majors"]
    other = next(m for m in allm if m["id"] not in mids)
    assert (
        staff.post(
            "/api/manage/curricula", json={"degree_name": "QA", "major_id": other["id"]}
        ).status_code
        == 403
    )


def test_intent_crud(admin):
    name = "QA-" + uuid.uuid4().hex[:8]
    payload = {
        "intent_name": name,
        "action_type": "rule_based",
        "static_response": "ทดสอบระบบ",
        "prompt_context": name,
        "is_active": True,
    }
    r = admin.post("/api/manage/intents", json=payload)
    assert r.status_code == 200
    id = r.json()["id"]
    try:
        payload["description"] = "แก้ไขแล้ว"
        assert admin.put(f"/api/manage/intents/{id}", json=payload).status_code == 200
        assert any(
            x["id"] == id for x in admin.get("/api/manage/intents?q=" + name).json()
        )
    finally:
        assert admin.delete(f"/api/manage/intents/{id}").status_code == 200


def test_validation(admin, staff):
    assert (
        admin.post(
            "/api/manage/majors",
            json={"major_name_th": "test", "website_url": "javascript:alert(1)"},
        ).status_code
        == 422
    )
    assert (
        staff.post(
            "/api/manage/careers",
            json={"job_title": "test", "salary_start": -1, "work_sector": "n"},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/uploads", files={"file": ("evil.svg", b"<svg/>", "image/svg+xml")}
        ).status_code
        == 422
    )
    me = admin.get("/api/auth/me").json()
    assert admin.delete("/api/manage/users/" + str(me["id"])).status_code == 422


def test_private_chat_feedback_and_rating():
    with TestClient(app) as a, TestClient(app) as b:
        a.get("/api/conversations")
        b.get("/api/conversations")
        conv = a.post("/api/conversations").json()
        id = conv["id"]
        try:
            assert b.get("/api/conversations/" + id).status_code == 404
            r = a.post(
                "/api/conversations/" + id + "/messages", json={"message": "สวัสดี"}
            )
            assert r.status_code == 200
            msg = r.json()
            assert msg["answer_mode"] == "rule_based"
            assert (
                b.patch(
                    f'/api/messages/{msg["id"]}/feedback', json={"is_helpful": True}
                ).status_code
                == 404
            )
            assert (
                a.patch(
                    f'/api/messages/{msg["id"]}/feedback', json={"is_helpful": True}
                ).json()["is_helpful"]
                is True
            )
            assert (
                a.patch("/api/conversations/" + id, json={"rating": 5}).json()["rating"]
                == 5
            )
            assert (
                a.patch("/api/conversations/" + id, json={"rating": 6}).status_code
                == 422
            )
            assert a.get("/api/conversations/" + id).json()[0]["is_helpful"] is True
            assert (
                a.patch(
                    "/api/conversations/" + id, json={"title": "QA renamed"}
                ).json()["title"]
                == "QA renamed"
            )
        finally:
            assert a.delete("/api/conversations/" + id).status_code == 200
        assert a.get("/api/conversations/" + id).status_code == 404


def test_logout(admin):
    assert admin.post("/api/auth/logout").status_code == 200
    assert admin.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    "entity,payload",
    [
        ("majors", {"major_name_th": "QA สาขาทดสอบ"}),
        (
            "general",
            {
                "topic": "QA ข้อมูลทดสอบ",
                "description": "ข้อมูลสำหรับตรวจสอบการบันทึกและค้นหาภายในระบบเท่านั้น ไม่ใช่ข้อมูลมหาวิทยาลัย",
            },
        ),
        (
            "news",
            {
                "title": "QA ข่าวทดสอบ",
                "content": "เนื้อหาสำหรับทดสอบการจัดการข่าวสารของระบบ",
            },
        ),
        (
            "careers",
            {
                "job_title": "QA อาชีพทดสอบ",
                "work_sector": "n",
                "job_description": "ข้อมูลสำหรับทดสอบระบบเท่านั้น",
            },
        ),
        (
            "users",
            {
                "username": "qa_" + uuid.uuid4().hex[:8],
                "fullname": "QA ผู้ใช้ทดสอบ",
                "password": uuid.uuid4().hex,
                "role": "staff",
                "major_ids": [],
                "active": True,
            },
        ),
        (
            "curricula",
            {
                "degree_name": "QA หลักสูตรทดสอบ",
                "major_id": 1,
                "career_ids": [],
                "description": "หลักสูตรสำหรับทดสอบระบบ ไม่ใช่หลักสูตรที่เปิดสอน",
            },
        ),
    ],
)
def test_entity_create_update_delete(admin, staff, entity, payload):
    admin = staff if entity in ("curricula", "careers") else admin
    if entity == "curricula":
        payload = {**payload, "major_id": staff.get("/api/auth/me").json()["major_ids"][0]}
    r = admin.post("/api/manage/" + entity, json=payload)
    assert r.status_code == 200, r.text
    id = r.json()["id"]
    try:
        assert any(x["id"] == id for x in admin.get("/api/manage/" + entity).json())
        label = next(
            k
            for k in (
                "major_name_th",
                "topic",
                "title",
                "job_title",
                "fullname",
                "degree_name",
            )
            if k in payload
        )
        payload = {**payload, label: payload[label] + " แก้ไข"}
        r = admin.put(f"/api/manage/{entity}/{id}", json=payload)
        assert r.status_code == 200, r.text
        assert r.json()[label].endswith("แก้ไข")
    finally:
        assert admin.delete(f"/api/manage/{entity}/{id}").status_code == 200
    with Session() as db:
        assert (
            db.scalar(
                select(Document).where(
                    Document.record_type == entity, Document.record_id == id
                )
            )
            is None
        )


def test_report_aggregation(admin, staff):
    data = admin.get("/api/reports/satisfaction").json()
    assert sum(data["rating_distribution"].values()) == data["rating_count"]
    assert data["likes"] + data["dislikes"] <= data["messages"]
    assert "daily" not in staff.get("/api/reports/satisfaction").json()
    assert admin.get("/api/reports/usage?start=invalid").status_code == 422


def test_admin_scope_boundaries(admin):
    for entity in ("curricula", "careers"):
        route = "/api/manage/" + entity
        assert admin.get(route).status_code == 403
        assert admin.post(route, json={}).status_code == 403
        assert admin.put(route + "/1", json={}).status_code == 403
        assert admin.delete(route + "/1").status_code == 403
    assert admin.patch("/api/profile", json={"fullname": "QA"}).status_code == 403


def test_dictionary_validation(admin, staff):
    for entity, payload in [
        ('general', {'topic':'QA'}), ('news', {'title':'QA'}),
        ('majors', {'major_name_th':None}),
        ('majors', {'major_name_th':'x'*256}),
        ('majors', {'major_name_th':'QA', 'tel':'1'*21}),
        ('majors', {'major_name_th':{'bad':'type'}}),
    ]:
        assert admin.post('/api/manage/'+entity, json=payload).status_code == 422
    mid = staff.get('/api/auth/me').json()['major_ids'][0]
    for extra in [{'total_credits':1.5}, {'curriculum_year':True}, {'career_ids':['invalid']}, {'tuition_fee':1.001}]:
        assert staff.post('/api/manage/curricula', json={'degree_name':'QA', 'major_id':mid, **extra}).status_code == 422
    assert staff.patch('/api/profile', json={'tel_no':'1'*21}).status_code == 422
    assert staff.patch('/api/profile', json={'fullname':''}).status_code == 422


def test_news_views_and_editor(admin):
    payload = {'title':'QA counter', 'content':'QA public news counter and last editor test'}
    r = admin.post('/api/manage/news', json=payload)
    assert r.status_code == 200
    item = r.json()
    try:
        assert item['views_count'] == 0
        with Session() as db:
            row = db.get(MODELS['news'], item['id'])
            row.user_id = None
            db.commit()
        updated = admin.put('/api/manage/news/'+str(item['id']), json={**payload,'views_count':999}).json()
        assert updated['user_id'] == admin.get('/api/auth/me').json()['id']
        assert updated['views_count'] == 0
        one = admin.get('/api/records/news/'+str(item['id'])).json()
        two = admin.get('/api/records/news/'+str(item['id'])).json()
        assert one['views_count'] == 1 and two['views_count'] == 2
        assert one['updated_at'] == two['updated_at']
    finally:
        admin.delete('/api/manage/news/'+str(item['id']))


def test_uploaded_pdf_index_and_decimal(staff):
    import io
    from pypdf import PdfWriter
    from pypdf.generic import NameObject, DecodedStreamObject, DictionaryObject
    from backend.db import ROOT
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'), NameObject('/Subtype'):NameObject('/Type1'), NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 10 100 Td (SCI_QA_PDF_evidence_731 academic guidance document for indexing test.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    buf = io.BytesIO(); writer.write(buf)
    upload = staff.post('/api/uploads', files={'file':('qa.pdf',buf.getvalue(),'application/pdf')})
    assert upload.status_code == 200
    url = upload.json()['url']
    item_id = None
    try:
        mid = staff.get('/api/auth/me').json()['major_ids'][0]
        payload = {'degree_name':'QA upload', 'major_id':mid, 'tuition_fee':1234.56, 'file_url':url}
        r = staff.post('/api/manage/curricula', json=payload)
        assert r.status_code == 200, r.text
        item_id = r.json()['id']
        assert r.json()['tuition_fee'] == 1234.56
        with Session() as db:
            doc = db.scalar(select(Document).where(Document.record_type=='curricula', Document.record_id==item_id))
            chunks = db.scalars(select(Chunk).where(Chunk.document_id==doc.id)).all()
            assert any('SCI_QA_PDF_evidence_731' in c.content for c in chunks)
            row = db.get(MODELS['curricula'], item_id)
            row.user_id = None
            db.commit()
        r = staff.put('/api/manage/curricula/'+str(item_id), json=payload)
        assert r.status_code == 200 and r.json()['user_id'] == staff.get('/api/auth/me').json()['id']
        assert staff.get(url).status_code == 200
    finally:
        if item_id:
            staff.delete('/api/manage/curricula/'+str(item_id))
        (ROOT / 'data/uploads' / url.rsplit('/',1)[-1]).unlink(missing_ok=True)
