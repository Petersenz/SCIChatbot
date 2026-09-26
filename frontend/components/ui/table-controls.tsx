"use client";
import {useId, useRef, useState, type ReactNode} from "react";
import {FiSliders, FiChevronDown, FiArrowUp, FiArrowDown, FiChevronsUp, FiX, FiRotateCcw, FiCheck, FiSearch} from "react-icons/fi";
import {activeFilter, filterError, optionsFor, type Column, type Filters, type Sort, type TableRow} from "./table-query";

export function SortHeading({column, sort, onChange}: {column: Column; sort: Sort; onChange: (sort: Sort) => void}) {
  const selected = sort?.key === column.key;
  const next = !selected ? {key:column.key, direction:"asc" as const} : sort.direction === "asc" ? {key:column.key, direction:"desc" as const} : null;
  const Icon = selected ? sort.direction === "asc" ? FiArrowUp : FiArrowDown : FiChevronsUp;
  return <th scope="col" aria-sort={selected ? sort.direction === "asc" ? "ascending" : "descending" : "none"}>
    <button type="button" className={"sort-heading" + (selected ? " selected" : "")} onClick={() => onChange(next)} title={!next ? "คืนลำดับเดิม" : next.direction === "asc" ? "เรียงน้อยไปมาก / ก–ฮ" : "เรียงมากไปน้อย / ฮ–ก"}>
      {column.label}<Icon aria-hidden="true" />
    </button>
  </th>;
}
export function TableControls({title, columns, rows, filters, onChange, resultCount, report=false, exportable=false}: {title: ReactNode; columns: Column[]; rows: TableRow[]; filters: Filters; onChange: (filters: Filters) => void; resultCount:number; report?:boolean; exportable?:boolean}) {
  const [open,setOpen]=useState(false), [draft,setDraft]=useState<Filters>({}), [error,setError]=useState("");
  const id=useId(), trigger=useRef<HTMLButtonElement>(null);
  const active=columns.filter(c=>filters[c.key] && activeFilter(filters[c.key]));
  const update=(key:string, part:Filters[string])=>{setDraft(old=>({...old,[key]:{...old[key],...part}}));setError("");};
  const close=()=>{setOpen(false);trigger.current?.focus();};
  const reset=()=>{setDraft({});setError("");onChange({});};
  return <div className="table-controls">
    <div className="table-toolbar"><h2>{title}</h2>
      <button ref={trigger} type="button" className={"filter-trigger"+(active.length ? " has-filters" : "")} aria-expanded={open} aria-controls={id} onClick={()=>{if(!open){setDraft(filters);setError("");}setOpen(!open);}}>
        <FiSliders aria-hidden="true"/> ตัวกรอง{active.length > 0 && <span className="filter-count">{active.length}</span>}<FiChevronDown aria-hidden="true" className={open ? "rotated" : ""}/>
      </button>
    </div>
    {open && <form id={id} className="table-filter-panel" aria-label="ตัวกรองตาราง" onKeyDown={e=>{if(e.key==="Escape"){e.stopPropagation();close();}}} onSubmit={e=>{e.preventDefault();const error=filterError(columns,draft);setError(error);if(!error){onChange(draft);close();}}}>
      <div className="filter-intro"><span><FiSliders aria-hidden="true"/> กรองตามข้อมูลในตาราง</span><small>เลือกได้หลายเงื่อนไข · เว้นว่างเพื่อแสดงทั้งหมด</small></div>
      <div className="table-filter-grid">{columns.map(c=>{
        const f=draft[c.key] || {}, controlId=id+"-"+c.key;
        return <div className="table-filter-field" key={c.key}>
          {c.kind === "number" || c.kind === "date" ? <fieldset><legend>{c.label}{c.kind === "number" && /salary|tuition/.test(c.key) ? " (บาท)" : ""}</legend><div className="filter-range">
            <label htmlFor={controlId+"-min"}>{c.kind === "date" ? "ตั้งแต่วันที่" : "ต่ำสุด"}<input id={controlId+"-min"} type={c.kind === "date" ? "date" : "number"} min={c.kind === "number" ? "0" : undefined} step={c.kind === "number" ? "any" : undefined} value={f.min || ""} placeholder="ไม่จำกัด" onChange={e=>update(c.key,{min:e.target.value})}/></label>
            <span aria-hidden="true">–</span><label htmlFor={controlId+"-max"}>{c.kind === "date" ? "ถึงวันที่" : "สูงสุด"}<input id={controlId+"-max"} type={c.kind === "date" ? "date" : "number"} min={c.kind === "number" ? "0" : undefined} step={c.kind === "number" ? "any" : undefined} value={f.max || ""} placeholder="ไม่จำกัด" onChange={e=>update(c.key,{max:e.target.value})}/></label>
          </div></fieldset> : <><label htmlFor={controlId}>{c.label}</label>{c.kind === "select" ? <select id={controlId} value={f.value || ""} onChange={e=>update(c.key,{value:e.target.value})}><option value="">ทั้งหมด</option>{optionsFor(c,rows).map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select> : <div className="filter-text"><FiSearch aria-hidden="true"/><input id={controlId} type="search" value={f.text || ""} placeholder={"ระบุ"+c.label} onChange={e=>update(c.key,{text:e.target.value})}/></div>}</>}
        </div>;
      })}</div>
      {error && <p role="alert" className="alert">{error}</p>}
      <div className="filter-actions"><button type="button" onClick={reset}><FiRotateCcw aria-hidden="true"/> ล้างตัวกรอง</button><button type="submit" className="primary"><FiCheck aria-hidden="true"/> ใช้ตัวกรอง</button></div>
    </form>}
    <div className="filter-summary"><span role="status" aria-live="polite">แสดง {resultCount.toLocaleString("th-TH")} จาก {rows.length.toLocaleString("th-TH")} รายการ</span>
      {active.map(c=>{const f=filters[c.key];const label=c.kind === "select" ? optionsFor(c,rows).find(o=>o.value===f.value)?.label || "ค่าที่เลือกไม่มีในข้อมูลปัจจุบัน" : c.kind === "text" ? f.text : `${f.min || "ไม่จำกัด"} – ${f.max || "ไม่จำกัด"}`;return <button type="button" className="filter-chip" key={c.key} aria-label={"ล้างตัวกรอง "+c.label} onClick={()=>{const next={...filters};delete next[c.key];onChange(next);setDraft(next);}}><span>{c.label}: {label}</span><FiX aria-hidden="true"/></button>;})}
      {active.length > 0 && <button type="button" className="filter-clear" onClick={reset}><FiRotateCcw aria-hidden="true"/> ล้างทั้งหมด</button>}
      {report && <small>ตัวกรองนี้ใช้กับรายการในตาราง{exportable ? "และ CSV" : ""} · สรุปด้านบนอ้างอิงช่วงวันที่รายงาน</small>}
    </div>
  </div>;
}
