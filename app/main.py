from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from .converter import markdown_to_pdf

app = FastAPI(
    title="markdown-pdf",
    description="Convert Markdown to PDF with GitHub-flavoured styling",
    version="1.0.0",
)


# ── models ────────────────────────────────────────────────────────────────────


class ConvertRequest(BaseModel):
    markdown: str
    filename: str = "document"


# ── routes ────────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(_UI_HTML)


@app.post("/convert")
def convert_json(req: ConvertRequest):
    """Accept a JSON body and return a PDF file download."""
    try:
        pdf = markdown_to_pdf(req.markdown, title=req.filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    safe_name = Path(req.filename).stem or "document"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )


@app.post("/convert/file")
async def convert_file(file: UploadFile):
    """Accept a .md file upload and return a PDF file download."""
    if not file.filename or not file.filename.endswith((".md", ".markdown", ".txt")):
        raise HTTPException(
            status_code=422,
            detail="Upload a Markdown file (.md / .markdown / .txt)",
        )

    raw = await file.read()
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded") from exc

    try:
        pdf = markdown_to_pdf(source, title=Path(file.filename).stem)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    safe_name = Path(file.filename).stem
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )


# ── minimal web UI ────────────────────────────────────────────────────────────

_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>markdown-pdf</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen flex flex-col items-center py-12 px-4">
  <div class="w-full max-w-3xl">
    <h1 class="text-3xl font-semibold text-gray-800 mb-1">markdown → pdf</h1>
    <p class="text-gray-500 mb-8 text-sm">GitHub-flavoured output &mdash; paste or upload</p>

    <!-- tabs -->
    <div class="flex gap-2 mb-4">
      <button id="tab-paste" onclick="showTab('paste')"
        class="px-4 py-1.5 rounded-full text-sm font-medium bg-gray-900 text-white">
        Paste
      </button>
      <button id="tab-upload" onclick="showTab('upload')"
        class="px-4 py-1.5 rounded-full text-sm font-medium bg-white text-gray-600 border border-gray-300">
        Upload file
      </button>
    </div>

    <!-- paste panel -->
    <div id="panel-paste">
      <textarea id="markdown-input" rows="20"
        placeholder="# Hello World&#10;&#10;Paste your Markdown here…"
        class="w-full rounded-lg border border-gray-300 p-4 font-mono text-sm
               focus:outline-none focus:ring-2 focus:ring-gray-400 resize-y"></textarea>
      <button onclick="convertPaste()"
        class="mt-3 w-full py-2.5 rounded-lg bg-gray-900 text-white font-medium
               hover:bg-gray-700 transition-colors">
        Convert to PDF
      </button>
    </div>

    <!-- upload panel -->
    <div id="panel-upload" class="hidden">
      <label class="flex flex-col items-center justify-center w-full h-40 border-2
                     border-dashed border-gray-300 rounded-lg cursor-pointer
                     hover:border-gray-500 transition-colors bg-white">
        <span class="text-gray-500 text-sm" id="upload-label">Click or drag a .md file here</span>
        <input type="file" id="file-input" accept=".md,.markdown,.txt" class="hidden"
               onchange="updateLabel(this)" />
      </label>
      <button onclick="convertFile()"
        class="mt-3 w-full py-2.5 rounded-lg bg-gray-900 text-white font-medium
               hover:bg-gray-700 transition-colors">
        Convert to PDF
      </button>
    </div>

    <p id="status" class="mt-4 text-sm text-center text-gray-500 hidden"></p>
  </div>

  <script>
    function showTab(name) {
      ['paste', 'upload'].forEach(t => {
        document.getElementById('panel-' + t).classList.toggle('hidden', t !== name);
        const btn = document.getElementById('tab-' + t);
        btn.className = t === name
          ? 'px-4 py-1.5 rounded-full text-sm font-medium bg-gray-900 text-white'
          : 'px-4 py-1.5 rounded-full text-sm font-medium bg-white text-gray-600 border border-gray-300';
      });
    }

    function setStatus(msg, isError) {
      const el = document.getElementById('status');
      el.textContent = msg;
      el.className = 'mt-4 text-sm text-center ' + (isError ? 'text-red-500' : 'text-gray-500');
      el.classList.remove('hidden');
    }

    function triggerDownload(blob, filename) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    }

    async function convertPaste() {
      const md = document.getElementById('markdown-input').value.trim();
      if (!md) { setStatus('Nothing to convert.', true); return; }
      setStatus('Converting…');
      try {
        const res = await fetch('/convert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ markdown: md, filename: 'document' }),
        });
        if (!res.ok) { setStatus('Error: ' + (await res.json()).detail, true); return; }
        triggerDownload(await res.blob(), 'document.pdf');
        setStatus('Done! PDF downloaded.');
      } catch (e) { setStatus('Request failed: ' + e.message, true); }
    }

    async function convertFile() {
      const input = document.getElementById('file-input');
      if (!input.files.length) { setStatus('No file selected.', true); return; }
      const form = new FormData();
      form.append('file', input.files[0]);
      setStatus('Converting…');
      try {
        const res = await fetch('/convert/file', { method: 'POST', body: form });
        if (!res.ok) { setStatus('Error: ' + (await res.json()).detail, true); return; }
        const name = input.files[0].name.replace(/\\.(md|markdown|txt)$/i, '') + '.pdf';
        triggerDownload(await res.blob(), name);
        setStatus('Done! PDF downloaded.');
      } catch (e) { setStatus('Request failed: ' + e.message, true); }
    }

    function updateLabel(input) {
      document.getElementById('upload-label').textContent =
        input.files[0] ? input.files[0].name : 'Click or drag a .md file here';
    }
  </script>
</body>
</html>"""
