import type {Config} from "../config";
export type TableRow = Record<string, any>;
export type Column = {key: string; label: string; kind: "text" | "select" | "number" | "date"; labelValue?: (value: any) => string};
export type Filter = {text?: string; value?: string; min?: string; max?: string};
export type Filters = Record<string, Filter>;
export type Sort = {key: string; direction: "asc" | "desc"} | null;
export const EMPTY = "__missing_value__";
const collator = new Intl.Collator("th", {numeric: true, sensitivity: "base"});
const missing = (v: any) => v === null || v === undefined || v === "";
export const normalized = (v: any) => String(v ?? "").normalize("NFC").trim().toLocaleLowerCase("th");
export const day = (v: any) => {
  if (missing(v) || !Number.isFinite(new Date(v).getTime())) return "";
  const parts = new Intl.DateTimeFormat("en-CA", {timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit"}).formatToParts(new Date(v));
  const get = (type: string) => parts.find(p => p.type === type)?.value;
  return `${get("year")}-${get("month")}-${get("day")}`;
};
export const activeFilter = (f: Filter) => Object.values(f).some(v => v !== undefined && v !== "");
export function optionsFor(column: Column, rows: TableRow[]) {
  return [...new Set(rows.map(r => missing(r[column.key]) ? EMPTY : String(r[column.key])))].map(value => ({
    value, label: value === EMPTY ? "ยังไม่ระบุ" : column.labelValue?.(value) ?? value,
  })).sort((a,b) => a.value === EMPTY ? 1 : b.value === EMPTY ? -1 : collator.compare(a.label, b.label));
}
export function filterError(columns: Column[], filters: Filters) {
  for (const c of columns) {
    const f = filters[c.key];
    if (!f || !activeFilter(f)) continue;
    if (c.kind === "number" && [f.min, f.max].some(v => v !== undefined && v !== "" && (!Number.isFinite(Number(v)) || Number(v) < 0))) return `${c.label}: กรุณาระบุตัวเลขตั้งแต่ 0 ขึ้นไป`;
    if (f.min && f.max && (c.kind === "number" ? Number(f.min) > Number(f.max) : f.min > f.max)) return `${c.label}: ค่าต่ำสุดต้องไม่มากกว่าค่าสูงสุด`;
  }
  return "";
}
export function queryRows(rows: TableRow[], columns: Column[], filters: Filters, sort: Sort) {
  const selected = rows.filter(row => columns.every(c => {
    const f = filters[c.key];
    if (!f || !activeFilter(f)) return true;
    const value = row[c.key];
    if (c.kind === "text") return normalized(value).includes(normalized(f.text));
    if (c.kind === "select") return (missing(value) ? EMPTY : String(value)) === f.value;
    if (missing(value)) return false;
    const comparable = c.kind === "date" ? day(value) : Number(value);
    if (comparable === "" || (typeof comparable === "number" && !Number.isFinite(comparable))) return false;
    return (!f.min || comparable >= (c.kind === "number" ? Number(f.min) : f.min)) && (!f.max || comparable <= (c.kind === "number" ? Number(f.max) : f.max));
  }));
  const c = columns.find(c => c.key === sort?.key);
  if (!c || !sort) return selected;
  return selected.sort((a,b) => {
    const av = a[c.key], bv = b[c.key];
    if (missing(av) || missing(bv)) return missing(av) === missing(bv) ? 0 : missing(av) ? 1 : -1;
    const order = c.kind === "number" ? Number(av) - Number(bv) : c.kind === "date" ? new Date(av).getTime() - new Date(bv).getTime() : collator.compare(c.labelValue?.(av) ?? String(av), c.labelValue?.(bv) ?? String(bv));
    return (sort.direction === "asc" ? 1 : -1) * (Number.isFinite(order) ? order : 0);
  });
}
export function managementColumns(cfg: Config, lookups: TableRow): Column[] {
  return cfg.columns.map(key => {
    const field = cfg.fields.find(f => f.key === key);
    const kind = key === "created_at" ? "date" : key === "curriculum_year" || ["select", "checkbox", "major"].includes(field?.type || "") ? "select" : field?.type === "number" ? "number" : "text";
    return {key, label: field?.label || "วันที่เพิ่ม", kind,
      labelValue: (v: any) => key === "major_id" ? String(lookups.majors?.find((r: TableRow) => String(r.id) === String(v))?.major_name_th ?? v) : field?.type === "checkbox" ? String(v) === "true" ? "เปิดใช้งาน" : "ปิดใช้งาน" : field?.options?.find(o => o[0] === String(v))?.[1] ?? String(v),
    };
  });
}
export function reportColumns(kind: string): Column[] {
  return [
    {key:"user_query", label:"คำถาม", kind:"text"},
    {key:"timestamp", label:"วันที่", kind:"date"},
    {key:"is_answered", label:"สถานะ", kind:"select", labelValue:v => String(v) === "true" ? "ตอบได้" : "ตอบไม่ได้"},
    kind === "unanswered" ? {key:"resolved", label:"ตรวจสอบ", kind:"select", labelValue:v => String(v) === "true" ? "ตรวจสอบแล้ว" : "รอตรวจสอบ"} : {key:"is_helpful", label:"ผลตอบรับ", kind:"select", labelValue:v => String(v) === "true" ? "ถูกใจ" : "ไม่ถูกใจ"},
  ];
}
