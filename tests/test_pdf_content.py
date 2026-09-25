import io
import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject, DecodedStreamObject, DictionaryObject
from test_large_pdf import pdf_fixture
from backend.text_processing import inspect_pdf, PDFValidationError
from test_api import staff
from backend.db import ROOT, Session, Document, Chunk, MODELS
from sqlalchemy import select


def mixed_pdf(scan=False, inline=False):
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(pdf_fixture(1))))
    page = writer.add_blank_page(width=200, height=200) if scan else writer.pages[0]
    image = DecodedStreamObject()
    image.update({NameObject('/Type'): NameObject('/XObject'), NameObject('/Subtype'): NameObject('/Image'),
                  NameObject('/Width'): NumberObject(1), NameObject('/Height'): NumberObject(1),
                  NameObject('/ColorSpace'): NameObject('/DeviceRGB'), NameObject('/BitsPerComponent'): NumberObject(8)})
    image.set_data(b'\xff\x00\x00')
    resources = page.get('/Resources', DictionaryObject())
    if not inline:
        resources[NameObject('/XObject')] = DictionaryObject({NameObject('/Im1'): writer._add_object(image)})
    page[NameObject('/Resources')] = resources
    contents = page.get_contents().get_data() if page.get_contents() is not None else b''
    contents += b'\nq BI /W 1 /H 1 /CS /RGB /BPC 8 ID \xff\x00\x00 EI Q' if inline else b'\nq 100 0 0 100 0 0 cm /Im1 Do Q'
    stream = DecodedStreamObject(); stream.set_data(contents)
    page[NameObject('/Contents')] = writer._add_object(stream)
    out = io.BytesIO(); writer.write(out)
    return out.getvalue()


def test_mixed_image_warns_without_embedding_warning_or_pixels(tmp_path):
    path = tmp_path/'mixed.pdf'; path.write_bytes(mixed_pdf())
    result = inspect_pdf(path)
    assert 'EvidencePage001' in result.text
    assert any('รูปภาพ' in w for w in result.warnings)
    assert all(w not in result.text for w in result.warnings)


@pytest.mark.parametrize('inline', [False, True])
def test_text_plus_scan_does_not_silently_succeed(tmp_path, inline):
    path = tmp_path/'scan.pdf'; path.write_bytes(mixed_pdf(scan=True, inline=inline))
    with pytest.raises(PDFValidationError, match='หน้า 2'):
        inspect_pdf(path)


def test_corrupt_pdf_not_cached_as_success(tmp_path):
    path = tmp_path/'bad.pdf'; path.write_bytes(b'%PDF-1.4\nbroken')
    with pytest.raises(Exception): inspect_pdf(path)


def test_attachments_and_fields_warn(tmp_path):
    writer = PdfWriter(); writer.append(PdfReader(io.BytesIO(pdf_fixture(1))))
    writer.add_attachment('extra.txt', b'NOT_INDEXED_ATTACHMENT')
    writer._root_object[NameObject('/AcroForm')] = DictionaryObject({NameObject('/NeedAppearances'): NameObject('/True')})
    path = tmp_path/'attachments.pdf'
    with path.open('wb') as stream: writer.write(stream)
    result = inspect_pdf(path)
    assert len(result.warnings) == 2
    assert 'NOT_INDEXED_ATTACHMENT' not in result.text


def test_media_api_warning_and_scan_rollback(staff, monkeypatch):
    urls = []; item = None
    try:
        for scan in (False, True):
            response = staff.post('/api/uploads', files={'file': ('media.pdf', mixed_pdf(scan), 'application/pdf')})
            assert response.status_code == 200
            urls.append(response.json()['url'])
        mid = staff.get('/api/auth/me').json()['major_ids'][0]
        payload = {'degree_name':'QA media CS', 'major_id':mid, 'curriculum_year':2598, 'file_url':urls[0]}
        response = staff.post('/api/manage/curricula', json=payload)
        assert response.status_code == 200, response.text
        item = response.json()['id']
        assert any('รูปภาพ' in w for w in response.json()['ingestion_warnings'])
        with Session() as db:
            doc = db.scalar(select(Document).where(Document.record_type=='curricula', Document.record_id==item))
            before = sorted(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id)))
        response = staff.put(f'/api/manage/curricula/{item}', json={**payload, 'file_url':urls[1]})
        assert response.status_code == 422 and 'หน้า 2' in response.json()['detail']
        with Session() as db:
            assert db.get(MODELS['curricula'],item).file_url == urls[0]
            assert sorted(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id))) == before
        assert (ROOT/'data/uploads'/urls[0].rsplit('/',1)[-1]).read_bytes() == mixed_pdf()
        import backend.rag as rag
        calls = []
        original_embed = rag.embed
        with monkeypatch.context() as patch:
            def track(texts):
                calls.extend(texts)
                return original_embed(texts)
            patch.setattr(rag, 'embed', track)
            payload['degree_name'] = 'QA media CS revised'
            response = staff.put(f'/api/manage/curricula/{item}', json=payload)
            assert response.status_code == 200
        assert 0 < len(calls) < len(before)
        with Session() as db:
            before = sorted(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id)))
        with monkeypatch.context() as patch:
            def fail(_): raise RuntimeError('QA embedding failure')
            patch.setattr(rag, 'embed', fail)
            with pytest.raises(RuntimeError, match='QA embedding failure'):
                staff.put(f'/api/manage/curricula/{item}', json={**payload, 'degree_name':'QA changed'})
        with Session() as db:
            assert db.get(MODELS['curricula'],item).degree_name == payload['degree_name']
            assert sorted(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id))) == before
    finally:
        if item: staff.delete(f'/api/manage/curricula/{item}')
        for url in urls: (ROOT/'data/uploads'/url.rsplit('/',1)[-1]).unlink(missing_ok=True)


def test_embedding_every_token_and_normalized(monkeypatch):
    import backend.rag as rag
    import numpy as np
    rag.embed(['warmup'])
    short = ['วิทย์คอม ปี 2570 เทอมแรกเรียนอะไรบ้าง']
    expected = rag._model.encode(short, normalize_embeddings=True, show_progress_bar=False)
    assert np.allclose(rag.embed(short), expected, atol=1e-5)
    original = rag._model.forward
    seen = []
    def capture(features, **kwargs):
        seen.extend(features['attention_mask'].sum(dim=1).tolist())
        return original(features, **kwargs)
    monkeypatch.setattr(rag._model, 'forward', capture)
    text = ('ข้อมูลหลักสูตรวิทยาการคอมพิวเตอร์ ระบบฐานข้อมูล ' * 35) + ' SCCS9999 TailUnique'
    tokens = rag._model.tokenizer(text, add_special_tokens=False, truncation=False)['input_ids']
    vectors = rag.embed([text])
    special = rag._model.tokenizer.num_special_tokens_to_add(pair=False)
    assert len(seen) > 1 and max(seen) <= rag._model.max_seq_length
    assert sum(n-special for n in seen) == len(tokens)
    assert len(vectors[0]) == 768 and np.isfinite(vectors).all()
    assert np.linalg.norm(vectors[0]) == pytest.approx(1.0, abs=1e-5)
