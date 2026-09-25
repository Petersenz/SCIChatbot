"""PDF text preparation; preserves page and semester boundaries for evidence."""
import re, logging, time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from pypdf import PdfReader


def normalize_text(value):
    # Legacy Thai font glyphs observed in the faculty's PDFs. Do not drop unknown glyphs.
    value = value.translate(str.maketrans({
        '\uf702': 'ี', '\uf703': 'ึ', '\uf70a': '่',
        '\uf70b': '้', '\uf70e': '์', '\uf710': 'ั',
    }))
    value = re.sub(r'(?<=[ก-๙]) +(?=[ัิีึืุู่้๊๋์])', '', value)
    return '\n'.join(re.sub(r'[ \t]+', ' ', line).strip() for line in value.splitlines())


MAX_PDF_PAGES = 250
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_PDF_CHARACTERS = 2_000_000


class PDFValidationError(ValueError):
    pass


def extract_pdf(path):
    return inspect_pdf(path).text


@dataclass(frozen=True)
class PDFExtraction:
    text: str
    warnings: tuple[str, ...]


def inspect_pdf(path):
    path = Path(path).resolve()
    stat = path.stat()
    if stat.st_size > MAX_PDF_BYTES:
        raise PDFValidationError('ไฟล์ PDF ต้องมีขนาดไม่เกิน 32 MB')
    return _extract_pdf(str(path), stat.st_mtime_ns, stat.st_size)


def _has_image(resources, seen=None):
    # Inspect object metadata only; never decode image pixels to build text vectors.
    seen = set() if seen is None else seen
    resources = resources.get_object() if resources else {}
    objects = resources['/XObject'].get_object() if '/XObject' in resources else {}
    for ref in objects.values():
        obj = ref.get_object()
        identity = id(obj)
        if identity in seen:
            continue
        seen.add(identity)
        if obj.get('/Subtype') == '/Image':
            return True
        if obj.get('/Subtype') == '/Form' and _has_image(obj.get('/Resources'), seen):
            return True
    return False


@lru_cache(maxsize=4)
def _extract_pdf(path, modified, size):
    started = time.perf_counter()
    # Cache immutable uploads so editing tuition does not parse 200 pages again.
    with open(path, 'rb') as stream:
        reader = PdfReader(stream)
        if reader.is_encrypted:
            raise PDFValidationError('กรุณาใช้ PDF ที่ไม่ตั้งรหัสผ่าน')
        if len(reader.pages) > MAX_PDF_PAGES:
            raise PDFValidationError(f'รองรับ PDF ไม่เกิน {MAX_PDF_PAGES} หน้า กรุณาแบ่งไฟล์ก่อนนำเข้า')
        parts, characters, readable = [], 0, 0
        image_pages, unreadable_pages, graphic_pages = [], [], []
        annotations = False
        for n, page in enumerate(reader.pages, 1):
            content = normalize_text(page.extract_text(extraction_mode='layout', layout_mode_strip_rotated=False) or '') if '/Contents' in page else ''
            has_image = _has_image(page.get('/Resources'))
            if not has_image and '/Contents' in page:
                # Inline images live in the drawing stream, not /XObject resources.
                has_image = any(operator == b'INLINE IMAGE' for _, operator in page.get_contents().operations)
            if has_image:
                image_pages.append(n)
                if not content.strip():
                    unreadable_pages.append(n)
            elif not content.strip() and '/Contents' in page:
                graphic_pages.append(n)
            annotations |= bool(page.get('/Annots'))
            readable += bool(content.strip())
            part = f'[หน้า {n}]\n{content}'
            characters += len(part) + 1
            if characters > MAX_PDF_CHARACTERS:
                raise PDFValidationError('ข้อความใน PDF มากเกินขีดจำกัด 2,000,000 ตัวอักษร กรุณาแบ่งไฟล์')
            parts.append(part)
        if not readable:
            raise PDFValidationError('ไม่พบข้อความที่อ่านได้ใน PDF ไฟล์สแกนต้องแปลงเป็นข้อความก่อน')
        if unreadable_pages:
            pages = ', '.join(map(str, unreadable_pages[:20]))
            raise PDFValidationError(f'อ่านข้อมูลจากรูปภาพไม่ได้ในหน้า {pages} กรุณาทำ OCR ให้เป็นข้อความก่อนบันทึก ข้อมูลเดิมยังไม่เปลี่ยน')
        warnings = []
        if image_pages:
            warnings.append('PDF มีรูปภาพ ระบบค้นจากข้อความเท่านั้น ข้อความในรูปและแผนภาพยังไม่ได้อ่าน กรุณาตรวจเทียบไฟล์ต้นฉบับ')
        if graphic_pages:
            warnings.append('ไม่พบข้อความในหน้า ' + ', '.join(map(str, graphic_pages[:20])) + ' กรุณาตรวจว่าเป็นหน้าว่างหรือข้อมูลแบบภาพ')
        if annotations or reader.trailer['/Root'].get('/AcroForm'):
            warnings.append('PDF มีหมายเหตุ ลิงก์ หรือช่องกรอกข้อมูล ส่วนเหล่านี้ไม่ได้ใช้เป็นหลักฐานสำหรับคำตอบ')
        names = reader.trailer['/Root'].get('/Names')
        if names and names.get_object().get('/EmbeddedFiles'):
            warnings.append('ไฟล์แนบภายใน PDF ไม่ได้นำเข้าเป็นข้อมูลค้นหา')
        logging.getLogger('uvicorn.error').info('pdf_extracted pages=%s readable_pages=%s image_pages=%s characters=%s seconds=%.3f', len(parts), readable, len(image_pages), characters, time.perf_counter()-started)
        return PDFExtraction('\n'.join(parts), tuple(warnings))


def split_evidence(value, size=1000):
    value = normalize_text(value)
    pages = re.split(r'(?=\[หน้า \d+\])', value)
    result = []
    active_heading = ''
    for page in pages:
        label = re.match(r'\[หน้า \d+\]', page)
        prefix = label.group(0) + '\n' if label else ''
        first_line = next((line.strip() for line in page.splitlines()
                           if line.strip() and not re.fullmatch(r'\[หน้า \d+\]', line.strip())), '')
        # Carry only an actual continuation row, not a new chapter, appendix,
        # or prose following a study plan in a long curriculum document.
        if label and not re.match(r'(?:[A-Z]{4}\d{4}\b|รวม\s+\d|หรือ\s*$)', first_line):
            active_heading = ''
        sections = re.split(r'(?=ปีที่\s*\d+\s*/\s*ภาคการศึกษาที่\s*\d+)', page)
        for section in sections:
            heading = re.match(r'ปีที่\s*\d+\s*/\s*ภาคการศึกษาที่\s*\d+', section)
            if heading:
                active_heading = heading.group(0)
            # A table can continue onto the next PDF page without repeating its
            # semester heading. Keep it until an explicit next semester begins.
            carry = prefix + (active_heading + '\n' if active_heading else '')
            current = carry
            for line in section.splitlines():
                if not line.strip():
                    continue
                # Long unbroken lines must not bypass the chunk size limit.
                if len(line) > size - len(carry) - 1:
                    if current != carry:
                        result.append(current.strip())
                        current = carry
                    width = max(100, size - len(carry) - 1)
                    for offset in range(0, len(line), width):
                        result.append((carry + line[offset:offset + width]).strip())
                    continue
                if len(current) + len(line) > size and current != carry:
                    result.append(current.strip())
                    current = carry
                current += line + '\n'
            if current.strip() and current != carry:
                result.append(current.strip())
    return result
