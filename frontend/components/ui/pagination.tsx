"use client";
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";

export function pageItems(page: number, pages: number): (number | string)[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
  if (page <= 4) return [1, 2, 3, 4, 5, "end", pages];
  if (page >= pages - 3) return [1, "start", pages - 4, pages - 3, pages - 2, pages - 1, pages];
  return [1, "start", page - 1, page, page + 1, "end", pages];
}

type Props = {
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
};

export function Pagination({ total, page, pageSize, onPageChange, onPageSizeChange }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.max(1, Math.min(page, pages));
  return (
    <div className="table-pagination">
      <span className="pagination-summary" role="status">
        {total ? `${(current - 1) * pageSize + 1}–${Math.min(current * pageSize, total)} จาก ${total.toLocaleString("th-TH")} รายการ` : "0 รายการ"}
      </span>
      <label className="pagination-size">
        รายการต่อหน้า
        <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
          {[10, 25, 50, 100].map((size) => <option key={size} value={size}>{size}</option>)}
        </select>
      </label>
      <nav className="pagination-pages" aria-label="แบ่งหน้ารายการ">
        <button type="button" className="page-direction" disabled={current === 1} onClick={() => onPageChange(current - 1)} aria-label="หน้าก่อนหน้า">
          <FiChevronLeft aria-hidden="true" /><span>ก่อนหน้า</span>
        </button>
        {pageItems(current, pages).map((item) => typeof item === "number" ? (
          <button type="button" key={item} className="page-number" aria-label={`หน้า ${item}`} aria-current={item === current ? "page" : undefined} disabled={total === 0} onClick={() => onPageChange(item)}>{item}</button>
        ) : <span key={item} className="page-gap" aria-hidden="true">…</span>)}
        <button type="button" className="page-direction" disabled={current === pages} onClick={() => onPageChange(current + 1)} aria-label="หน้าถัดไป">
          <span>ถัดไป</span><FiChevronRight aria-hidden="true" />
        </button>
      </nav>
    </div>
  );
}
