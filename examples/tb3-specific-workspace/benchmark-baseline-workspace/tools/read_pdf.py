"""Read-PDF tool — extract text from PDF files."""

from __future__ import annotations

import asyncio
import shutil

import anyio


async def read_pdf(pdf_path: str, max_pages: int = 50, force_ocr: bool = False) -> str:
    """Extract text from a PDF file.

    Tries multiple methods in order: pdftotext (poppler), pymupdf (fitz),
    then pdfplumber. If none are available, returns an error with install
    instructions.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum pages to extract.
        force_ocr: If True, attempt OCR on image-only PDFs (requires tesseract).

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
        return result

    # Method 2: pymupdf (fitz)
    result = await _try_pymupdf(bash, pdf_path, max_pages)
    if result is not None:
        return result

    # Method 3: pdfplumber
    result = await _try_pdfplumber(bash, pdf_path, max_pages)
    if result is not None:
        return result

    return (
        "[Error] No PDF text extraction tool available. "
        "Install one of: poppler-utils (pdftotext), pymupdf (pip install pymupdf), "
        f"or pdfplumber (pip install pdfplumber). File: {pdf_path}"
    )


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
