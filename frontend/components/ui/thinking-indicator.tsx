"use client";
import {useEffect,useState} from "react";
import {ShiningText} from "./shining-text";
export function ThinkingIndicator() {
 const [slow,setSlow]=useState(false);
 useEffect(()=>{const timer=setTimeout(()=>setSlow(true),12000);return ()=>clearTimeout(timer);},[]);
 return <div className="thinking-status" role="status" aria-live="polite" aria-atomic="true"><ShiningText text="SCIChatbot is thinking..."/>{slow && <small>ใช้เวลานานกว่าปกติ กรุณารอสักครู่ ยังไม่ต้องส่งคำถามซ้ำ</small>}</div>;
}
