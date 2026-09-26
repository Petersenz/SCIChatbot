"use client";
import { FlowButton } from "@/components/ui/flow-button";
export function FlowButtonDemo() { return <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4"><FlowButton text="Flow Button" /></div>; }
export function FlowButtonStates() { return <div className="p-4"><FlowButton text="เริ่มสนทนาใหม่" /><FlowButton text="ชี้เมาส์เพื่อทดสอบ Hover" /><FlowButton text="กด Tab เพื่อทดสอบ Focus" /><FlowButton text="กดค้างเพื่อทดสอบ Active" /><FlowButton text="ปิดใช้งาน" disabled /><FlowButton text="กำลังทำงาน" state="loading" /><FlowButton text="ลองใหม่" state="error" /><FlowButton text="เรียบร้อย" state="success" /></div>; }
export default FlowButtonDemo;
