"use client";
import {ShiningText} from "./shining-text";
import {StatusNotice} from "./status-notice";
export function ShiningTextDemo(){return <ShiningText text="SCIChatbot is thinking..."/>;}
export function StatusNoticeDemo(){return <><StatusNotice tone="info">กำลังตรวจสอบข้อมูล</StatusNotice><StatusNotice tone="warning">ใช้เวลานานกว่าปกติ กรุณารอสักครู่</StatusNotice><StatusNotice>เชื่อมต่อไม่สำเร็จ กรุณาตรวจสอบอินเทอร์เน็ต</StatusNotice></>;}
