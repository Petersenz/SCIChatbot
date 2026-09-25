"use client";
import { useEffect, useState, useRef, FormEvent } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  FiMenu,
  FiPlus,
  FiArrowUp,
  FiMessageSquare,
  FiThumbsUp,
  FiThumbsDown,
  FiStar,
  FiX,
  FiEdit2,
  FiTrash2,
  FiHome,
  FiUsers,
  FiBookOpen,
  FiBriefcase,
  FiInfo,
  FiFileText,
  FiGrid,
  FiBarChart2,
  FiHelpCircle,
  FiUser,
  FiLogOut,
  FiSearch,
  FiArrowLeft,
  FiExternalLink,
  FiDownload,
  FiCheck,
} from "react-icons/fi";
import { api, configs, Field } from "./config";
type Row = Record<string, any>;
const titles: Record<string, string> = {
  dashboard: "ภาพรวมระบบ",
  usage: "รายงานสถิติการใช้งาน",
  satisfaction: "รายงานคะแนนความพึงพอใจ",
  unanswered: "รายงานคำถามที่ตอบไม่ได้",
  profile: "จัดการข้อมูลส่วนตัว",
};
const icons: Record<string, any> = {
  dashboard: FiHome,
  users: FiUsers,
  majors: FiGrid,
  general: FiInfo,
  news: FiFileText,
  intents: FiMessageSquare,
  curricula: FiBookOpen,
  careers: FiBriefcase,
  usage: FiBarChart2,
  satisfaction: FiStar,
  unanswered: FiHelpCircle,
  profile: FiUser,
};
function Mark({ large = false }: { large?: boolean }) {
  return (
    <span className={"mark logo-mark " + (large ? "large" : "")}>
      <img src="/brand/sci-chatbot.png" alt={large ? "SCI Chatbot" : ""} width={1254} height={1254} />
    </span>
  );
}
function Modal({
  title,
  children,
  close,
}: {
  title: string;
  children: React.ReactNode;
  close: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (trigger?.isConnected) trigger.focus();
    };
  }, []);
  return (
    <dialog ref={ref} onCancel={close} aria-labelledby="dialog-title" onKeyDown={(event) => {
      if (event.key !== 'Tab') return;
      const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex="0"]'
      )).filter(el => el.getClientRects().length > 0);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }}>
      <div className="dialog-head">
        <h2 id="dialog-title">{title}</h2>
        <button className="icon" onClick={close} aria-label="ปิด">
          <FiX />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export default function App() {
  const path = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<Row | null>(null);
  const [checked, setChecked] = useState(false);
  const [menu, setMenu] = useState(false);
  const [error, setError] = useState("");
  const admin = path.startsWith("/admin");
  const page = path.split("/")[2] || "dashboard";
  useEffect(() => {
    if (!admin && path !== "/login") {
      setChecked(true);
      return;
    }
    api("/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecked(true));
  }, []);
  useEffect(() => {
    setMenu(false);
    setError("");
  }, [path]);
  useEffect(() => {
    if (checked && admin && !user) router.replace("/login");
  }, [checked, admin, user, router]);
  async function logout() {
    await api("/auth/logout", "POST");
    setUser(null);
    router.push("/login");
  }
  if (path === "/login")
    return (
      <Login
        onLogin={(u) => {
          setUser(u);
          router.push(
            u.role === "admin" ? "/admin/dashboard" : "/admin/curricula",
          );
        }}
      />
    );
  if (path.startsWith("/records/")) return <RecordView path={path} />;
  if (!admin) return <ChatApp />;
  if (!checked || !user)
    return (
      <main id="main" className="loading">
        กำลังโหลด…
      </main>
    );
  const links =
    user.role === "admin"
      ? [
          "dashboard",
          "users",
          "majors",
          "general",
          "news",
          "intents",
          "usage",
          "satisfaction",
          "unanswered",
        ]
      : ["curricula", "careers", "satisfaction", "unanswered", "profile"];
  if (!links.includes(page))
    return (
      <main id="main" className="loading">
        <h1>ไม่มีสิทธิ์เข้าถึงหน้านี้</h1>
        <a href={user.role === "admin" ? "/admin/dashboard" : "/admin/profile"}>
          กลับหน้าหลัก
        </a>
      </main>
    );
  return (
    <div className="admin-shell">
      <header className="admin-top">
        <button
          className="icon mobile-toggle"
          aria-label="เปิดเมนู"
          aria-expanded={menu}
          onClick={() => setMenu(!menu)}
        >
          <FiMenu />
        </button>
        <span className="breadcrumb">
          Dashboard <span>/</span> {configs[page]?.title || titles[page]}
        </span>
        <div className="account">
          <span>
            {user.fullname}
            <small>
              {user.role === "admin" ? "ผู้ดูแลระบบ" : "เจ้าหน้าที่"}
            </small>
          </span>
          <span className="avatar" aria-hidden="true"><FiUser /></span>
        </div>
      </header>
      {menu && (
        <button
          className="scrim"
          aria-label="ปิดเมนู"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={"admin-side " + (menu ? "open" : "")}>
        <a className="brand" href="/">
          <Mark />
          <strong>ไซน์แชทบอท</strong>
        </a>
        <p className="side-label">จัดการระบบ</p>
        <nav aria-label="เมนูจัดการ">
          {links.map((k) => {
            const Icon = icons[k];
            return (
              <a
                key={k}
                className={page === k ? "active" : ""}
                href={"/admin/" + k}
                aria-current={page === k ? "page" : undefined}
              >
                <Icon />
                <span>
                  {configs[k]?.title
                    .replace("ของคณะวิทยาศาสตร์และเทคโนโลยี", "")
                    .replace(" (Intent)", "") || titles[k]}
                </span>
              </a>
            );
          })}
        </nav>
        <div className="side-bottom">
          <a href="/">
            <FiMessageSquare /> หน้าสนทนา
          </a>
          <button onClick={logout}>
            <FiLogOut /> ออกจากระบบ
          </button>
        </div>
      </aside>
      <main id="main" className="admin-main">
        {error && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}
        {configs[page] ? (
          <Management key={page} entity={page} user={user} />
        ) : page === "profile" ? (
          <Profile user={user} onChange={setUser} />
        ) : (
          <Reports kind={page} />
        )}
      </main>
    </div>
  );
}
function Login({ onLogin }: { onLogin: (u: Row) => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      onLogin(await api("/auth/login", "POST", data));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="login-page">
      <a className="back" href="/">
        <FiArrowLeft /> กลับหน้าสนทนา
      </a>
      <div className="login-card">
        <Mark large />
        <h1>เข้าสู่ระบบ</h1>
        <p className="muted">สำหรับผู้ดูแลระบบและเจ้าหน้าที่</p>
        <form onSubmit={submit}>
          <label>
            ชื่อผู้ใช้
            <input name="username" autoComplete="username" required autoFocus />
          </label>
          <label>
            รหัสผ่าน
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {error && (
            <p className="alert" role="alert">
              {error}
            </p>
          )}
          <button className="primary wide" disabled={busy}>
            {busy ? "กำลังเข้าสู่ระบบ…" : "เข้าสู่ระบบ"}
          </button>
        </form>
        <p className="login-footer">
          คณะวิทยาศาสตร์และเทคโนโลยี
          <br />
          มหาวิทยาลัยราชภัฏเพชรบูรณ์
        </p>
      </div>
    </main>
  );
}
function ChatApp() {
  const [sessions, setSessions] = useState<Row[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [messages, setMessages] = useState<Row[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [menu, setMenu] = useState(false);
  const [modal, setModal] = useState<"rename" | "delete" | "rate" | null>(null);
  const [dismissed, setDismissed] = useState<string[]>([]);
  const end = useRef<HTMLDivElement>(null);
  const composerInput = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    const el = composerInput.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  }, [input]);
  const current = sessions.find((s) => s.id === active);
  useEffect(() => {
    api("/conversations")
      .then(setSessions)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);
  async function refresh() {
    setSessions(await api("/conversations"));
  }
  async function select(s: Row) {
    if (busy) return;
    try {
      setMessages(await api("/conversations/" + s.id));
      setActive(s.id);
      setMenu(false);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function reset() {
    setActive(null);
    setMessages([]);
    setInput("");
    setMenu(false);
  }
  async function send(text = input) {
    if (!text.trim() || busy) return;
    setBusy(true);
    setError("");
    setInput("");
    try {
      let id = active;
      if (!id) {
        const s = await api("/conversations", "POST");
        id = s.id;
        setActive(id);
      }
      const pending = { id: -1, user_query: text, bot_response: "" };
      setMessages((m) => [...m, pending]);
      const item = await api("/conversations/" + id + "/messages", "POST", {
        message: text,
      });
      setMessages((m) => [...m.filter((x) => x.id !== -1), item]);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
      setMessages((m) => m.filter((x) => x.id !== -1));
      setInput(text);
    } finally {
      setBusy(false);
    }
  }
  async function feedback(m: Row, value: boolean) {
    try {
      const x = await api("/messages/" + m.id + "/feedback", "PATCH", {
        is_helpful: m.is_helpful === value ? null : value,
      });
      setMessages((ms) => ms.map((v) => (v.id === x.id ? x : v)));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function rate(n: number) {
    try {
      await api("/conversations/" + active, "PATCH", { rating: n });
      await refresh();
      setModal(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const suggestions = [
    ["สาขาวิชา", "คณะวิทยาศาสตร์ มีสาขาอะไรบ้าง?", FiBookOpen],
    ["ค่าบำรุงการศึกษา", "ค่าเทอมแต่ละสาขาเท่าไหร่?", FiFileText],
    ["การรับสมัคร", "สมัครเรียนต้องใช้เอกสารอะไรบ้าง?", FiUsers],
    ["อาชีพหลังจบการศึกษา", "จบไปแล้วทำงานอะไรได้บ้าง?", FiBriefcase],
  ] as const;
  return (
    <div className="chat-shell">
      <header className="chat-top">
        <button
          className="icon mobile-toggle"
          aria-label="เปิดประวัติการสนทนา"
          aria-expanded={menu}
          onClick={() => setMenu(!menu)}
        >
          <FiMenu />
        </button>
        <a className="brand" href="/">
          <Mark />
          <strong>ไซน์แชทบอท</strong>
        </a>
        <a className="login-link" href="/login">
          <FiUser /> เข้าสู่ระบบ
        </a>
      </header>
      {menu && (
        <button
          className="scrim"
          aria-label="ปิดประวัติการสนทนา"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={"chat-side " + (menu ? "open" : "")}>
        <button
          className="primary wide"
          disabled={busy}
          onClick={() => {
            if (
              active &&
              messages.length >= 3 &&
              !current?.rating &&
              !dismissed.includes(active)
            )
              setModal("rate");
            else reset();
          }}
        >
          <FiPlus /> เริ่มสนทนาใหม่
        </button>
        <p className="side-label">ประวัติการสนทนา</p>
        <nav aria-label="ประวัติการสนทนา">
          {sessions.length === 0 ? (
            <p className="muted empty-history">ยังไม่มีประวัติการสนทนา</p>
          ) : (
            sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => select(s)}
                disabled={busy}
                className={"history " + (s.id === active ? "selected" : "")}
              >
                <FiMessageSquare />
                <span>{s.title}</span>
              </button>
            ))
          )}
        </nav>
        <div className="side-bottom muted">SCI Chatbot v1.0</div>
      </aside>
      <main id="main" className="chat-main">
        {active && (
          <div className="conversation-bar">
            <span>{current?.title || "บทสนทนาใหม่"}</span>
            <button
              className="icon"
              aria-label="แก้ไขชื่อการสนทนา"
              onClick={() => setModal("rename")}
              disabled={busy}
            >
              <FiEdit2 />
            </button>
            <button
              className="icon"
              aria-label="ลบบทสนทนา"
              onClick={() => setModal("delete")}
              disabled={busy}
            >
              <FiTrash2 />
            </button>
            <button
              className="icon"
              aria-label="ประเมินบทสนทนา"
              onClick={() => setModal("rate")}
              disabled={busy}
            >
              <FiStar />
            </button>
          </div>
        )}
        <div className="chat-scroll">
          {messages.length === 0 ? (
            <section className="welcome">
              <Mark large />
              <h1>
                ยินดีต้อนรับสู่ <span>ไซน์แชทบอท</span>
              </h1>
              <p>
                ค้นหาข้อมูลคณะวิทยาศาสตร์และเทคโนโลยีได้ง่ายๆ
                <br />
                เพียงพิมพ์คำถามที่คุณสนใจหรือเลือกหัวข้อแนะนำด้านล่าง
              </p>
              <div className="suggestions">
                {suggestions.map(([title, q, Icon]) => (
                  <button key={title} onClick={() => send(q)} disabled={busy}>
                    <Icon />
                    <strong>{title}</strong>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <div
              className="messages"
              role="log"
              aria-label="ข้อความสนทนา"
              aria-live="polite"
            >
              {messages.map((m) => (
                <div key={m.id} className="turn">
                  <div className="user-message">{m.user_query}</div>
                  {m.bot_response && (
                    <div className="bot-row">
                      <Mark />
                      <div className="bot-content">
                        <div className="bot-message">{m.bot_response}</div>
                        {m.sources?.filter((s: Row) => s.image_url).map((s: Row) => (
                          <a className="answer-image" key={s.url} href={s.url} target="_blank" rel="noopener noreferrer">
                            {/* Existing source image, never a model-generated URL. */}
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={s.image_url} alt={s.title} loading="lazy" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                            <span>{s.title}</span>
                          </a>
                        ))}
                        {m.sources?.length > 0 && (
                          <details className="sources">
                            <summary>แหล่งข้อมูล ({m.sources.length})</summary>
                            {m.sources.map((s: Row, i: number) => (
                              <a
                                href={s.url}
                                key={s.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <span>
                                  {i + 1}. {s.title}
                                </span>
                                <FiExternalLink />
                              </a>
                            ))}
                          </details>
                        )}
                        <div className="feedback">
                          <button
                            aria-label="ถูกใจคำตอบ"
                            aria-pressed={m.is_helpful === true}
                            className="icon"
                            onClick={() => feedback(m, true)}
                          >
                            <FiThumbsUp />
                          </button>
                          <button
                            aria-label="ไม่ถูกใจคำตอบ"
                            aria-pressed={m.is_helpful === false}
                            className="icon"
                            onClick={() => feedback(m, false)}
                          >
                            <FiThumbsDown />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {busy && (
                <p role="status" className="typing">
                  กำลังค้นหาข้อมูล<span>…</span>
                </p>
              )}
              <div ref={end} />
            </div>
          )}
        </div>
        {error && (
          <p className="alert chat-error" role="alert">
            {error}
          </p>
        )}
        <div className="composer-wrap">
          {active &&
            messages.length >= 3 &&
            !current?.rating &&
            !dismissed.includes(active) && (
              <div className="rating-nudge">
                <button onClick={() => setModal("rate")}>
                  <FiStar /> ประเมินการสนทนา
                </button>
                <button
                  className="icon"
                  aria-label="ไว้ภายหลัง"
                  onClick={() => setDismissed([...dismissed, active])}
                >
                  <FiX />
                </button>
              </div>
            )}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <textarea
              ref={composerInput}
              aria-label="พิมพ์คำถาม"
              placeholder="พิมพ์คำถามที่คุณต้องการสอบถาม…"
              rows={1}
              maxLength={1500}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing
                ) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <button
              className="send"
              disabled={busy || !input.trim()}
              aria-label="ส่งข้อความ"
            >
              <FiArrowUp />
            </button>
          </form>
          <p className="disclaimer">
            SCI Chatbot อาจให้ข้อมูลที่คลาดเคลื่อน
            โปรดตรวจสอบข้อมูลที่เป็นทางการอีกครั้ง
          </p>
        </div>
      </main>
      {modal === "rename" && (
        <Modal title="แก้ไขชื่อการสนทนา" close={() => setModal(null)}>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api(
                  "/conversations/" + active,
                  "PATCH",
                  Object.fromEntries(new FormData(e.currentTarget)),
                );
                await refresh();
                setModal(null);
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            <label>
              ชื่อการสนทนา
              <input
                name="title"
                required
                maxLength={120}
                defaultValue={current?.title}
              />
            </label>
            <div className="actions">
              <button type="button" onClick={() => setModal(null)}>
                ยกเลิก
              </button>
              <button className="primary">บันทึก</button>
            </div>
          </form>
        </Modal>
      )}
      {modal === "delete" && (
        <Modal title="ลบบทสนทนา" close={() => setModal(null)}>
          <p>ต้องการลบบทสนทนานี้หรือไม่?</p>
          <div className="actions">
            <button onClick={() => setModal(null)}>ยกเลิก</button>
            <button
              className="danger"
              onClick={async () => {
                try {
                  await api("/conversations/" + active, "DELETE");
                  setModal(null);
                  reset();
                  await refresh();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              ลบบทสนทนา
            </button>
          </div>
        </Modal>
      )}
      {modal === "rate" && (
        <Modal title="ประเมินความพึงพอใจ" close={() => setModal(null)}>
          <p>คุณพึงพอใจกับการสนทนาครั้งนี้มากน้อยเพียงใด?</p>
          <div className="stars">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                aria-label={n + " ดาว"}
                aria-pressed={current?.rating === n}
                onClick={() => rate(n)}
              >
                <FiStar />
                <span>{n}</span>
              </button>
            ))}
          </div>
          <div className="actions">
            <button
              onClick={() => {
                if (active) setDismissed([...dismissed, active]);
                setModal(null);
                reset();
              }}
            >
              เริ่มสนทนาใหม่
            </button>
            <button onClick={() => setModal(null)}>ไว้ภายหลัง</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
function Management({ entity, user }: { entity: string; user: Row }) {
  const cfg = configs[entity];
  const [rows, setRows] = useState<Row[]>([]);
  const [lookups, setLookups] = useState<Row>({ majors: [], careers: [] });
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Row | null>(null);
  const [deleting, setDeleting] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(1);
  const load = () => api("/manage/" + entity).then(setRows);
  useEffect(() => {
    Promise.all([load(), api("/lookups").then(setLookups)]).catch((e) =>
      setError(e.message),
    );
  }, [entity]);
  const filtered = rows.filter((r) =>
    JSON.stringify(r).toLowerCase().includes(search.toLowerCase()),
  );
  const visible = filtered.slice((page - 1) * 8, page * 8);
  function display(r: Row, k: string) {
    const v = r[k];
    if (v == null || v === "") return "—";
    if (k === "major_id")
      return lookups.majors.find((x: Row) => x.id === v)?.major_name_th || v;
    if (k === "role") return v === "admin" ? "ผู้ดูแลระบบ" : "เจ้าหน้าที่";
    if (k === "action_type") return v === "rag" ? "RAG" : "คำตอบที่กำหนดไว้";
    if (k === "is_active")
      return (
        <span className={"badge " + (v ? "success" : "")}>
          {v ? "เปิดใช้งาน" : "ปิดใช้งาน"}
        </span>
      );
    if (k === "work_sector")
      return cfg.fields
        .find((f) => f.key === k)
        ?.options?.find((o) => o[0] === v)?.[1];
    if (k === "created_at") return new Date(v).toLocaleDateString("th-TH");
    if (typeof v === "number") return v.toLocaleString("th-TH");
    return String(v);
  }
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (e.currentTarget.querySelector('[data-uploading="true"]')) {
      setError("กรุณารอให้อัปโหลดไฟล์เสร็จก่อนบันทึก");
      return;
    }
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    const data: Row = {};
    for (const field of cfg.fields) {
      if (["majors", "careers"].includes(field.type || ""))
        data[field.key] = form.getAll(field.key).map(Number);
      else if (field.type === "checkbox") data[field.key] = form.has(field.key);
      else if (["number", "major"].includes(field.type || ""))
        data[field.key] =
          form.get(field.key) === "" ? null : Number(form.get(field.key));
      else data[field.key] = form.get(field.key) || "";
    }
    if (entity !== "users" && entity !== "intents")
      data.source_url = form.get("source_url") || "";
    try {
      const saved = await api(
        "/manage/" + entity + (editing?.id ? "/" + editing.id : ""),
        editing?.id ? "PUT" : "POST",
        data,
      );
      setEditing(null);
      await load();
      setNotice(["บันทึกข้อมูลแล้ว", ...(saved.ingestion_warnings || [])].join(" — "));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{cfg.title}</h1>
          <p className="muted">จัดการ{cfg.single}ในระบบ</p>
        </div>
        <button
          className="primary"
          onClick={() => {
            setError("");
            setEditing({
              active: true,
              is_active: true,
              role: "staff",
              action_type: "rag",
              work_sector: "",
            });
          }}
        >
          <FiPlus /> เพิ่ม{cfg.single}
        </button>
      </div>
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {error && !editing && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <section className="panel">
        <div className="table-toolbar">
          <h2>
            {cfg.single}ทั้งหมด <span className="count">{rows.length}</span>
          </h2>
          <div className="search">
            <FiSearch />
            <input
              aria-label={"ค้นหา" + cfg.single}
              placeholder="ค้นหา…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {cfg.columns.map((k) => (
                  <th key={k}>
                    {cfg.fields.find((f) => f.key === k)?.label ||
                      "วันที่เพิ่ม"}
                  </th>
                ))}
                <th>จัดการ</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => (
                <tr key={r.id}>
                  {cfg.columns.map((k, i) => (
                    <td key={k}>
                      <div className={i === 0 ? "row-title" : "cell-text"}>
                        {display(r, k)}
                      </div>
                    </td>
                  ))}
                  <td>
                    <div className="row-actions">
                      <button
                        className="icon"
                        aria-label={"แก้ไข " + display(r, cfg.columns[0])}
                        onClick={() => {
                          setError("");
                          setEditing(r);
                        }}
                      >
                        <FiEdit2 />
                      </button>
                      <button
                        className="icon delete"
                        aria-label={"ลบ " + display(r, cfg.columns[0])}
                        onClick={() => setDeleting(r)}
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {visible.length === 0 && <p className="empty">ไม่พบข้อมูล</p>}
        </div>
        <div className="pagination">
          <span>ทั้งหมด {filtered.length} รายการ</span>
          <button disabled={page === 1} onClick={() => setPage(page - 1)}>
            ก่อนหน้า
          </button>
          <span>
            {page} / {Math.max(1, Math.ceil(filtered.length / 8))}
          </span>
          <button
            disabled={page * 8 >= filtered.length}
            onClick={() => setPage(page + 1)}
          >
            ถัดไป
          </button>
        </div>
      </section>
      {editing && (
        <Modal
          title={(editing.id ? "แก้ไข" : "เพิ่ม") + cfg.single}
          close={() => {
            if (!busy) setEditing(null);
          }}
        >
          <form onSubmit={save}>
            <div className="form-grid">
              {cfg.fields.map((f) => (
                <FieldInput
                  key={f.key}
                  field={f.key === "password" ? { ...f, required: !editing.id } : f}
                  value={editing[f.key]}
                  lookups={lookups}
                  user={user}
                />
              ))}
              {entity !== "users" && entity !== "intents" && (
                <label className="full">
                  แหล่งข้อมูล
                  <input
                    type="url"
                    name="source_url"
                    defaultValue={editing.source_url || ""}
                  />
                </label>
              )}
            </div>
            {error && (
              <p role="alert" className="alert">
                {error}
              </p>
            )}
            <div className="actions">
              <button
                type="button"
                disabled={busy}
                onClick={() => setEditing(null)}
              >
                ยกเลิก
              </button>
              <button className="primary" disabled={busy}>
                {busy ? "กำลังบันทึก…" : "บันทึกข้อมูล"}
              </button>
            </div>
          </form>
        </Modal>
      )}
      {deleting && (
        <Modal title={"ลบ" + cfg.single} close={() => setDeleting(null)}>
          <p>ต้องการลบ “{display(deleting, cfg.columns[0])}” หรือไม่?</p>
          <div className="actions">
            <button onClick={() => setDeleting(null)}>ยกเลิก</button>
            <button
              className="danger"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await api("/manage/" + entity + "/" + deleting.id, "DELETE");
                  setDeleting(null);
                  await load();
                  setNotice("ลบข้อมูลแล้ว");
                } catch (e) {
                  setError((e as Error).message);
                  setDeleting(null);
                } finally {
                  setBusy(false);
                }
              }}
            >
              ลบข้อมูล
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
function FieldInput({
  field: f,
  value,
  lookups,
  user,
}: {
  field: Field;
  value: any;
  lookups: Row;
  user: Row;
}) {
  const [upload, setUpload] = useState(value || "");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  if (f.type === "checkbox")
    return (
      <label className="checkbox">
        <input type="checkbox" name={f.key} defaultChecked={!!value} />
        {f.label}
      </label>
    );
  if (f.type === "majors" || f.type === "careers") {
    const list = lookups[f.type] || [];
    return (
      <fieldset className="full">
        <legend>{f.label}</legend>
        {list.map((x: Row) => (
          <label className="checkbox" key={x.id}>
            <input
              type="checkbox"
              name={f.key}
              value={x.id}
              defaultChecked={value?.includes(x.id)}
            />
            {x.major_name_th || x.job_title}
          </label>
        ))}
      </fieldset>
    );
  }
  if (f.type === "upload")
    return (
      <label className="full">
        {f.label}
        <input
          name={f.key}
          value={upload}
          onChange={(e) => setUpload(e.target.value)}
          placeholder="วางลิงก์หรือเลือกไฟล์"
        />
        <input
          aria-label={"อัปโหลด" + f.label}
          type="file"
          accept={f.key === "file_url" ? ".pdf" : ".png,.jpg,.jpeg"}
          disabled={uploading}
          data-uploading={uploading ? "true" : "false"}
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            const extension = file.name.split('.').pop()?.toLowerCase() || '';
            if (!(f.key === 'file_url' ? ['pdf'] : ['png', 'jpg', 'jpeg']).includes(extension)) {
              setError(f.key === 'file_url' ? 'กรุณาเลือกไฟล์ PDF' : 'กรุณาเลือกไฟล์ PNG หรือ JPG');
              e.target.value = '';
              return;
            }
            const limit = (f.key === "file_url" ? 32 : 8) * 1024 * 1024;
            if (file.size > limit) { setError("ไฟล์มีขนาดเกินที่กำหนด"); return; }
            setUploading(true);
            const body = new FormData();
            body.append("file", file);
            try {
              const r = await fetch("/api/uploads", { method: "POST", body });
              const data = await r.json();
              if (!r.ok) throw new Error(data.detail);
              setUpload(data.url);
              setError("");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setUploading(false);
            }
          }}
        />
        {f.key === "file_url" && <small>PDF ไม่เกิน 32 MB และ 250 หน้า · อัปโหลดไฟล์เพื่อใช้ค้นหาข้อมูล ลิงก์ใช้เปิดต้นฉบับ</small>}
        {uploading && <span role="status">กำลังอัปโหลด…</span>}
        {error && <span role="alert">{error}</span>}
      </label>
    );
  return (
    <label className={f.type === "textarea" ? "full" : ""}>
      <span className="field-label">
        {f.label}{f.required && <span aria-hidden="true"> *</span>}
      </span>
      {f.type === "textarea" ? (
        <textarea
          name={f.key}
          rows={4}
          defaultValue={value || ""}
          required={f.required}
          maxLength={25000}
        />
      ) : f.type === "select" || f.type === "major" ? (
        <select name={f.key} defaultValue={value ?? ""} required={f.required}>
          <option value="">เลือก{f.label}</option>
          {f.type === "major"
            ? lookups.majors
                .filter(
                  (x: Row) =>
                    user.role === "admin" || user.major_ids.includes(x.id),
                )
                .map((x: Row) => (
                  <option key={x.id} value={x.id}>
                    {x.major_name_th}
                  </option>
                ))
            : f.options?.map(([v, t]) => (
                <option key={v} value={v}>
                  {t}
                </option>
              ))}
        </select>
      ) : (
        <input
          name={f.key}
          type={f.type}
          defaultValue={f.type === "password" ? "" : (value ?? "")}
          min={f.type === "number" ? 0 : undefined}
          step={f.type === "number" ? (["tuition_fee", "salary_start"].includes(f.key) ? "0.01" : "1") : undefined}
          minLength={f.type === "password" ? 10 : undefined}
          maxLength={f.type === 'password' ? 200 : ['tel', 'tel_no'].includes(f.key) ? 20 : 255}
          max={f.type === 'number' ? (['tuition_fee', 'salary_start'].includes(f.key) ? 99999999.99 : 2147483647) : undefined}
          autoComplete={f.type === "password" ? "new-password" : undefined}
          required={f.required}
        />
      )}
    </label>
  );
}
function Profile({
  user,
  onChange,
}: {
  user: Row;
  onChange: (u: Row) => void;
}) {
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>จัดการข้อมูลส่วนตัว</h1>
          <p className="muted">ข้อมูลบัญชีผู้ใช้งาน</p>
        </div>
      </div>
      <section className="panel profile-panel">
        <div className="profile-head">
          <span className="avatar large" aria-hidden="true"><FiUser /></span>
          <div>
            <h2>{user.fullname}</h2>
            <span className="muted">
              {user.role === "admin" ? "ผู้ดูแลระบบ" : "เจ้าหน้าที่"}
            </span>
          </div>
        </div>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              const data = Object.fromEntries(new FormData(e.currentTarget));
              const u = await api("/profile", "PATCH", data);
              onChange(u);
              setNotice(
                data.new_password
                  ? "เปลี่ยนรหัสผ่านแล้ว กรุณาเข้าสู่ระบบอีกครั้ง"
                  : "บันทึกข้อมูลแล้ว",
              );
              setError("");
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="form-grid">
            <label>
              ชื่อผู้ใช้
              <input value={user.username} disabled />
            </label>
            <label>
              ชื่อ–นามสกุล
              <input name="fullname" required defaultValue={user.fullname} />
            </label>
            <label>
              อีเมล
              <input name="email" type="email" defaultValue={user.email} />
            </label>
            <label>
              เบอร์โทรศัพท์
              <input name="tel_no" defaultValue={user.tel_no} />
            </label>
            <label>
              รหัสผ่านเดิม
              <input
                name="current_password"
                type="password"
                autoComplete="current-password"
              />
            </label>
            <label>
              รหัสผ่านใหม่
              <input
                name="new_password"
                type="password"
                minLength={10}
                autoComplete="new-password"
              />
            </label>
          </div>
          {error && (
            <p role="alert" className="alert">
              {error}
            </p>
          )}
          {notice && (
            <p role="status" className="notice">
              {notice}
            </p>
          )}
          <div className="actions">
            <button className="primary" disabled={busy}>
              บันทึกข้อมูล
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
function Reports({ kind }: { kind: string }) {
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, [filter, kind, data]);
  const load = () => {
    setError("");
    return api("/reports/" + kind + "?start=" + start + "&end=" + end)
      .then(setData)
      .catch((e) => { setData(null); setError(e.message); });
  };
  useEffect(() => {
    load();
  }, [kind]);
  const rows = (data?.rows || []).filter((r: Row) =>
    r.user_query.includes(filter),
  );
  function download() {
    const quote = (x: any) =>
      '"' +
      String(x ?? "")
        .replace(/^[=+@-]/, "'")
        .replaceAll('"', '""') +
      '"';
    const text =
      "\ufeff" +
      [
        ["คำถาม", "คำตอบ", "ตอบได้", "ถูกใจ", "วันที่"],
        ...rows.map((r: Row) => [
          r.user_query,
          r.bot_response,
          r.is_answered,
          r.is_helpful,
          r.timestamp,
        ]),
      ]
        .map((a) => a.map(quote).join(","))
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "sci-" + kind + ".csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{titles[kind]}</h1>
          <p className="muted">
            {kind === "dashboard"
              ? "ภาพรวมข้อมูลและการสนทนา"
              : "ข้อมูลจากการใช้งานระบบ"}
          </p>
        </div>
        {data && kind === "usage" && (
          <button onClick={download}>
            <FiDownload /> ส่งออก CSV
          </button>
        )}
      </div>
      {error && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <form
        className="date-filter"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <label>
          ตั้งแต่วันที่
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          ถึงวันที่
          <input
            type="date"
            value={end}
            min={start}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <button className="primary">แสดงข้อมูล</button>
      </form>
      {data && (
        <>
          <div className="stats">
            {(kind === "satisfaction"
              ? [
                  [
                    "คะแนนเฉลี่ย",
                    data.rating_average === null
                      ? "—"
                      : data.rating_average + " / 5",
                    FiStar,
                  ],
                  ["บทสนทนาที่ประเมิน", data.rating_count, FiMessageSquare],
                  ["ถูกใจ", data.likes, FiThumbsUp],
                  ["ไม่ถูกใจ", data.dislikes, FiThumbsDown],
                ]
              : kind === "unanswered"
                ? [
                    ["คำถามที่ตอบไม่ได้", data.unanswered, FiHelpCircle],
                    [
                      "ตรวจสอบแล้ว",
                      data.rows.filter((r: Row) => r.resolved).length,
                      FiCheck,
                    ],
                  ]
                : [
                    ["ผู้ใช้งาน", data.visitors, FiUsers],
                    ["คำถามทั้งหมด", data.messages, FiMessageSquare],
                    ["ตอบได้", data.answered, FiCheck],
                    ["คำถามที่ตอบไม่ได้", data.unanswered, FiHelpCircle],
                  ]
            ).map(([label, value, Icon]: any) => (
              <section className="stat" key={label}>
                <div>
                  <p>{label}</p>
                  <strong>{value}</strong>
                </div>
                <span className="stat-icon">
                  <Icon />
                </span>
              </section>
            ))}
          </div>
          {(kind === "dashboard" ||
            kind === "usage" ||
            kind === "satisfaction") && (
            <div className="report-grid">
              <section className="panel chart">
                <h2>
                  {kind === "satisfaction"
                    ? "คะแนนความพึงพอใจ"
                    : "จำนวนคำถามรายวัน"}
                </h2>
                {Object.entries(
                  kind === "satisfaction"
                    ? data.rating_distribution
                    : data.daily,
                ).length ? (
                  Object.entries(
                    kind === "satisfaction"
                      ? data.rating_distribution
                      : data.daily,
                  ).map(([k, v]) => (
                    <div className="bar-row" key={k}>
                      <span>{kind === "satisfaction" ? k + " ดาว" : k}</span>
                      <div className="bar-track">
                        <div
                          style={{
                            width:
                              Math.max(
                                0,
                                (Number(v) /
                                  Math.max(
                                    1,
                                    ...Object.values(
                                      kind === "satisfaction"
                                        ? data.rating_distribution
                                        : data.daily,
                                    ).map(Number),
                                  )) *
                                  100,
                              ) + "%",
                          }}
                        />
                      </div>
                      <strong>{String(v)}</strong>
                    </div>
                  ))
                ) : (
                  <p className="empty">ยังไม่มีข้อมูล</p>
                )}
              </section>
              <section className="panel chart">
                <h2>
                  {kind === "satisfaction"
                    ? "ผลตอบรับรายข้อความ"
                    : "ข้อมูลในระบบ"}
                </h2>
                {kind === "satisfaction" ? (
                  <>
                    <div className="feedback-summary">
                      <FiThumbsUp />
                      <strong>{data.likes}</strong>
                      <span>ถูกใจ</span>
                    </div>
                    <div className="feedback-summary">
                      <FiThumbsDown />
                      <strong>{data.dislikes}</strong>
                      <span>ไม่ถูกใจ</span>
                    </div>
                    <p className="muted">
                      คะแนนดาวประเมินรายบทสนทนา
                      <br />
                      ถูกใจ–ไม่ถูกใจประเมินรายคำตอบ
                    </p>
                  </>
                ) : (
                  Object.entries(data.data_counts)
                    .filter(
                      ([k]) =>
                        configs[k] && !["curricula", "careers"].includes(k),
                    )
                    .map(([k, v]) => (
                      <a className="summary-row" href={"/admin/" + k} key={k}>
                        <span>{configs[k].single}</span>
                        <strong>{String(v)}</strong>
                      </a>
                    ))
                )}
              </section>
            </div>
          )}
          <section className="panel">
            <div className="table-toolbar">
              <h2>
                {kind === "unanswered"
                  ? "รายการคำถามที่ตอบไม่ได้"
                  : "การสนทนาล่าสุด"}
              </h2>
              <div className="search">
                <FiSearch />
                <input
                  aria-label="ค้นหาคำถาม"
                  placeholder="ค้นหาคำถาม…"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>คำถาม</th>
                    <th>วันที่</th>
                    <th>สถานะ</th>
                    <th>{kind === "unanswered" ? "ตรวจสอบ" : "ผลตอบรับ"}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice((page - 1) * 30, page * 30).map((r: Row) => (
                    <tr key={r.id}>
                      <td>
                        <details>
                          <summary className="question-summary">
                            {r.user_query}
                          </summary>
                          <p className="answer-preview">{r.bot_response}</p>
                        </details>
                      </td>
                      <td>
                        {new Date(r.timestamp).toLocaleString("th-TH", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })}
                      </td>
                      <td>
                        <span
                          className={
                            "badge " + (r.is_answered ? "success" : "warning")
                          }
                        >
                          {r.is_answered ? "ตอบได้" : "ตอบไม่ได้"}
                        </span>
                      </td>
                      <td>
                        {kind === "unanswered" ? (
                          <button
                            onClick={async () => {
                              try {
                                await api("/unanswered/" + r.id, "PATCH", {
                                  resolved: !r.resolved,
                                });
                                load();
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            {r.resolved ? "ตรวจสอบแล้ว" : "รอตรวจสอบ"}
                          </button>
                        ) : r.is_helpful === null ? (
                          "—"
                        ) : r.is_helpful ? (
                          "ถูกใจ"
                        ) : (
                          "ไม่ถูกใจ"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {rows.length === 0 && <p className="empty">ยังไม่มีข้อมูล</p>}
            </div>
            <div className="pagination">
              <span>ทั้งหมด {rows.length} รายการ</span>
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>ก่อนหน้า</button>
              <span>{page} / {Math.max(1, Math.ceil(rows.length / 30))}</span>
              <button disabled={page * 30 >= rows.length} onClick={() => setPage(page + 1)}>ถัดไป</button>
            </div>
          </section>
        </>
      )}
    </>
  );
}
function RecordView({ path }: { path: string }) {
  const [row, setRow] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const recordConfig = configs[path.split('/')[2]];
  useEffect(() => {
    api(path)
      .then(setRow)
      .catch((e) => setError(e.message));
  }, [path]);
  return (
    <main id="main" className="record-page">
      <a href="/">← กลับหน้าสนทนา</a>
      {error && <p role="alert">{error}</p>}
      {row && (
        <>
          <h1>
            {row.topic ||
              row.title ||
              row.degree_name ||
              row.major_name_th ||
              row.job_title}
          </h1>
          <p className="record-text">
            {row.description || row.content || row.job_description}
          </p>
          {(row.image_url || row.cover_image) && (
            <img src={row.image_url || row.cover_image} alt={row.topic || row.title || ""} style={{maxWidth:"100%",maxHeight:400,objectFit:"contain"}} />
          )}
          <dl>
            {recordConfig?.fields.filter(f => !["description","content","job_description","topic","title","degree_name","major_name_th","job_title","file_url","image_url","cover_image","major_id","career_ids"].includes(f.key) && row[f.key] !== null && row[f.key] !== undefined && row[f.key] !== "").map(f => (
              <div key={f.key} style={{marginBottom:12}}>
                <dt style={{fontWeight:600}}>{f.label}</dt>
                <dd style={{margin:0,whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{f.options?.find(o=>o[0]===row[f.key])?.[1] || String(row[f.key])}</dd>
              </div>
            ))}
          </dl>
          {row.file_url && <p><a href={row.file_url} target="_blank" rel="noopener noreferrer">ไฟล์หลักสูตร (PDF)</a></p>}
          {row.source_url && (
            <a href={row.source_url} target="_blank" rel="noopener noreferrer">
              ดูแหล่งข้อมูลทางการ
            </a>
          )}
        </>
      )}
    </main>
  );
}
