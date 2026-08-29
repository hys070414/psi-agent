"""Read-PDF tool — extract text from PDF files."""

from __future__ import annotations

import asyncio
import glob
import shutil
import tempfile

import anyio

DEFAULT_MAX_CHARS = 50000
"""Hard cap on characters returned by read_pdf (guards the context window)."""


async def read_pdf(
    pdf_path: str,
    max_pages: int = 50,
    force_ocr: bool = False,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Extract text from a PDF file.

    Tries multiple methods in order: pdftotext (poppler), pymupdf (fitz),
    then pdfplumber. If *force_ocr* is True and no text layer was found,
    falls back to OCR via pdftoppm + tesseract (both must be on PATH).

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum pages to extract.
        force_ocr: If True, attempt OCR on image-only PDFs (requires tesseract + pdftoppm).
        max_chars: Maximum characters of extracted text to return.

    Returns:
        Extracted text, or an error message.
    """
    path = anyio.Path(pdf_path)
    if not await path.exists():
        return f"[Error] File not found: {pdf_path}"
    if not await path.is_file():
        return f"[Error] Not a file: {pdf_path}"

    bash = shutil.which("bash")
    if not bash:
        return "[Error] bash not found on PATH"

    # Method 1: pdftotext (poppler-utils)
    result = await _try_pdftotext(bash, pdf_path, max_pages)
    if result is not None:
        return _cap(result, max_chars)

    # Method 2: pymupdf (fitz)
    result = await _try_pymupdf(bash, pdf_path, max_pages)
    if result is not None:
        return _cap(result, max_chars)

    # Method 3: pdfplumber
    result = await _try_pdfplumber(bash, pdf_path, max_pages)
    if result is not None:
        return _cap(result, max_chars)

    # Method 4: OCR fallback for image-only / scanned PDFs
    if force_ocr:
        result = await _try_ocr(bash, pdf_path, max_pages)
        if result is not None:
            return _cap(result, max_chars)
        return (
            "[Error] OCR requested but pdftoppm/tesseract are not available, "
            f"or OCR produced no text. File: {pdf_path}"
        )

    return (
        "[Error] No PDF text extraction tool available. "
        "Install one of: poppler-utils (pdftotext), pymupdf (pip install pymupdf), "
        "or pdfplumber (pip install pdfplumber). For scanned/image-only PDFs, also "
        "install poppler-utils (pdftoppm) and tesseract, then call with force_ocr=True. "
        f"File: {pdf_path}"
    )


def _cap(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n... [truncated at {max_chars} chars, {len(text)} total]"


async def _try_pdftotext(bash: str, pdf_path: str, max_pages: int) -> str | None:
    if not shutil.which("pdftotext"):
        return None
    try:
        proc = await asyncio.create_subprocess_exec(
            bash,
            "-lc",
            f"pdftotext -l {max_pages} '{pdf_path}' - 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        text = stdout.decode(errors="replace").strip()
        return text or None
    except Exception:
        return None


async def _try_pymupdf(bash: str, pdf_path: str, max_pages: int) -> str | None:
    script = f"""python3 -c "
import sys
try:
    import fitz
except ImportError:
    sys.exit(1)
doc = fitz.open('{pdf_path}')
pages = []
for i, page in enumerate(doc):
    if i >= {max_pages}:
        break
    pages.append(page.get_text())
print(chr(10).join(pages))
" 2>/dev/null"""
    try:
        proc = await asyncio.create_subprocess_exec(
            bash,
            "-lc",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode == 0:
            text = stdout.decode(errors="replace").strip()
            return text or None
    except Exception:
        pass
    return None


async def _try_pdfplumber(bash: str, pdf_path: str, max_pages: int) -> str | None:
    script = f"""python3 -c "
import sys
try:
    import pdfplumber
except ImportError:
    sys.exit(1)
pages = []
with pdfplumber.open('{pdf_path}') as pdf:
    for i, page in enumerate(pdf.pages):
        if i >= {max_pages}:
            break
        pages.append(page.extract_text() or '')
print(chr(10).join(pages))
" 2>/dev/null"""
    try:
        proc = await asyncio.create_subprocess_exec(
            bash,
            "-lc",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode == 0:
            text = stdout.decode(errors="replace").strip()
            return text or None
    except Exception:
        pass
    return None


async def _try_ocr(bash: str, pdf_path: str, max_pages: int) -> str | None:
    """Render PDF pages to PNG with pdftoppm, then OCR each with tesseract."""
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        return None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            prefix = f"{tmp}/page"
            render_cmd = (
                f"pdftoppm -png -r 200 -f 1 -l {max_pages} '{pdf_path}' '{prefix}' 2>/dev/null"
            )
            proc = await asyncio.create_subprocess_exec(
                bash,
                "-lc",
                render_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=120)

            page_images = sorted(glob.glob(f"{prefix}-*.png"))
            if not page_images:
                return None

            texts = []
            for page_img in page_images:
                ocr_cmd = f"tesseract '{page_img}' stdout 2>/dev/null"
                proc = await asyncio.create_subprocess_exec(
                    bash,
                    "-lc",
                    ocr_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
                texts.append(stdout.decode(errors="replace").strip())

            result = "\n\n".join(t for t in texts if t).strip()
            return result or None
    except Exception:
        return None
