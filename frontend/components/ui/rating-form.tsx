"use client";
import {useId,useRef,useState} from "react";
import {Star,LoaderCircle} from "lucide-react";
import {StatusNotice} from "./status-notice";
const labels=["","น้อยที่สุด","น้อย","ปานกลาง","มาก","มากที่สุด"];
export function RatingForm({initial=0,onRate,onLater,onNew}: {initial?:number;onRate:(value:number)=>Promise<void>;onLater:()=>void;onNew:()=>void}) {
 const [value,setValue]=useState(initial);const [hover,setHover]=useState(0);
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");const lock=useRef(false);const id=useId();
 const shown=hover||value;
 return <form className="rating-form" aria-busy={busy} onSubmit={async event=>{
  event.preventDefault();if(!value||lock.current)return;lock.current=true;setBusy(true);setError("");
  try {await onRate(value);}catch(e){setError((e as Error).message);}finally{lock.current=false;setBusy(false);}
 }}>
  <p className="rating-question" id={id+"-question"}>คุณพึงพอใจกับการสนทนาครั้งนี้มากน้อยเพียงใด?</p>
  <fieldset className="rating-control" disabled={busy} aria-labelledby={id+"-question"}>
   <legend className="rating-sr-only">เลือกคะแนนความพึงพอใจ 1 ถึง 5 ดาว</legend>
   <div className="rating-star-row" onMouseLeave={()=>setHover(0)}>
    {[1,2,3,4,5].map(n=><label key={n} className={`rating-star ${n<=shown?"is-filled":""}`} onMouseEnter={()=>setHover(n)}>
     <input type="radio" name={id} value={n} checked={value===n} aria-label={`${n} ดาว — ${labels[n]}`} onChange={()=>{setValue(n);setHover(0);}}/>
     <Star aria-hidden="true"/><span className="rating-star-number" aria-hidden="true">{n}</span>
    </label>)}
   </div>
   <p className="rating-caption" aria-live="polite">{shown ? `${shown} / 5 · ${labels[shown]}` : "เลือกดาวเพื่อให้คะแนน"}</p>
  </fieldset>
  {error && <StatusNotice>{error}</StatusNotice>}
  <button className="primary wide rating-submit" type="submit" disabled={!value||busy}>{busy?<><LoaderCircle className="rating-spinner" aria-hidden="true"/>กำลังบันทึก…</>:"บันทึกคะแนน"}</button>
  <div className="rating-secondary"><button type="button" disabled={busy} onClick={onNew}>เริ่มสนทนาใหม่</button><button type="button" disabled={busy} onClick={onLater}>ไว้ภายหลัง</button></div>
 </form>;
}
