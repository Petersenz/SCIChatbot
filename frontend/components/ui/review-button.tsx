"use client";
import {useRef, useState} from "react";
import {FiCheckCircle, FiClock, FiLoader} from "react-icons/fi";

export function ReviewButton({resolved, onToggle, onError}: {
  resolved: boolean; onToggle: () => Promise<void>; onError: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  return <button type="button" className={`review-action ${resolved ? "is-reviewed" : "is-pending"}`}
    disabled={busy} aria-busy={busy} aria-pressed={resolved}
    title={resolved ? "เปลี่ยนกลับเป็นรอตรวจสอบ" : "ทำเครื่องหมายว่าตรวจสอบแล้ว"}
    onClick={async () => {
      if(lock.current) return;
      lock.current=true; setBusy(true);
      try { await onToggle(); } catch(error) { onError(error instanceof Error ? error.message : "บันทึกสถานะไม่สำเร็จ กรุณาลองใหม่"); }
      finally { lock.current=false; setBusy(false); }
    }}>
    {busy ? <FiLoader className="button-spinner" aria-hidden="true"/> : resolved ? <FiCheckCircle aria-hidden="true"/> : <FiClock aria-hidden="true"/>}
    <span>{busy ? "กำลังบันทึก…" : resolved ? "ตรวจสอบแล้ว" : "รอตรวจสอบ"}</span>
  </button>;
}
