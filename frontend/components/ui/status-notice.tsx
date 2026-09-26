"use client";
import type {ReactNode} from "react";
import {Info, TriangleAlert, CircleAlert} from "lucide-react";
export function StatusNotice({children, tone="error", className=""}: {children:ReactNode;tone?:"info"|"warning"|"error";className?:string}) {
  const Icon=tone==="error"?CircleAlert:tone==="warning"?TriangleAlert:Info;
  return <div className={`status-notice status-${tone} ${className}`} role={tone==="error"?"alert":"status"}><Icon aria-hidden="true"/><div>{children}</div></div>;
}
