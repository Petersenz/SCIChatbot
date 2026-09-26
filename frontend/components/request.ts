export class ApiError extends Error {
 constructor(message:string,public status=0,public code="network_error",public requestId="",public retryAfter:number|null=null){super(message);this.name="ApiError";}
}
export function remainingThinkingMs(started:number,now:number){return Math.max(0,1000-(now-started));}
export async function readApiResponse(response:Response,method="GET") {
 const write=!["GET","HEAD"].includes(method.toUpperCase());
 let data:any;
 const raw=await response.text();
 try { data=JSON.parse(raw); } catch { data=null; }
 const reference=data?.request_id || response.headers.get("X-Request-ID") || "";
 const id=/^[a-f0-9]{12}$/.test(reference)?reference:"";
 if(response.ok && data!==null)return data;
 const status=response.status;
 const defaults:Record<number,string>={401:"กรุณาเข้าสู่ระบบใหม่ หรือเปิดหน้าสนทนาอีกครั้ง",403:"ไม่มีสิทธิ์ดำเนินการนี้",404:"ไม่พบรายการนี้ กรุณาโหลดข้อมูลใหม่",409:"ข้อมูลอาจซ้ำหรือมีการเปลี่ยนแปลง กรุณาโหลดรายการเพื่อตรวจสอบ",413:"ไฟล์มีขนาดเกินที่กำหนด กรุณาลดขนาดไฟล์",422:"ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบช่องที่กรอก",429:"ส่งคำขอถี่เกินไป กรุณารอสักครู่ก่อนลองอีกครั้ง",502:"เชื่อมต่อบริการไม่ได้ชั่วคราว",503:"บริการยังไม่พร้อมใช้งาน กรุณาลองภายหลัง",504:"บริการใช้เวลาตอบกลับนานเกินไป"};
 const detail=typeof data?.detail==="string" && data.detail.length<500 && !/[<>]/.test(data.detail)?data.detail:"";
 let message=status<500 && detail?detail:defaults[status] || "ระบบขัดข้องชั่วคราว";
 if(write && (status>=500 || response.ok)) message+=" อาจมีการบันทึกแล้ว กรุณาตรวจสอบรายการหรือประวัติก่อนส่งซ้ำ";
 if(id)message+=` (รหัสอ้างอิง ${id})`;
 const wait=Number(response.headers.get("Retry-After"));
 if(status===429 && Number.isFinite(wait) && wait>0)message+=` รอประมาณ ${Math.ceil(wait)} วินาที`;
 throw new ApiError(message,status,data?.code || (response.ok?"invalid_response":"request_failed"),id,Number.isFinite(wait)&&wait>0?wait:null);
}
export async function requestJson(url:string,options:RequestInit={},timeoutMs=120000){
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeoutMs);
 try {
  return await readApiResponse(await fetch(url,{...options,signal:controller.signal}),options.method || "GET");
 } catch(error) {
  if(error instanceof ApiError)throw error;
  const timedOut=controller.signal.aborted;
  const write=!["GET","HEAD"].includes((options.method || "GET").toUpperCase());
  throw new ApiError((timedOut?"รอการตอบกลับนานเกินไป":"เชื่อมต่อไม่สำเร็จ กรุณาตรวจสอบอินเทอร์เน็ต")+(write?" อาจมีการบันทึกแล้ว กรุณาตรวจสอบรายการหรือประวัติก่อนส่งซ้ำ":" กรุณาลองโหลดข้อมูลอีกครั้ง"),0,timedOut?"timeout":"network_error");
 } finally {clearTimeout(timer);}
}
