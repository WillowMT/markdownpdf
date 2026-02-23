from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from .converter import markdown_to_html, markdown_to_pdf

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


@app.post("/preview", response_class=HTMLResponse)
def preview(req: ConvertRequest):
    """Return a browser-renderable HTML page for the live preview iframe."""
    try:
        html = markdown_to_html(req.markdown)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return HTMLResponse(html)


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


# ── UI ────────────────────────────────────────────────────────────────────────

_UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>markdown-pdf</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    html, body { height: 100%; overflow: hidden; }
    #editor {
      tab-size: 2;
      -moz-tab-size: 2;
      resize: none;
      outline: none;
    }
    #preview-frame { border: 0; flex: 1; width: 100%; }
    #divider { cursor: col-resize; }
    body.resizing { cursor: col-resize !important; user-select: none; }
    body.resizing #preview-frame { pointer-events: none; }
  </style>
</head>
<body class="h-screen flex flex-col bg-white text-gray-800">

  <!-- ── header ─────────────────────────────────────────────────── -->
  <header class="flex items-center justify-between px-5 py-2.5 border-b border-gray-200 bg-white shrink-0 gap-4">
    <div class="flex items-center gap-2 shrink-0">
      <span class="font-semibold text-sm text-gray-800">markdown → pdf</span>
      <span class="text-xs text-gray-400 hidden sm:inline">GitHub-flavoured</span>
    </div>

    <div class="flex items-center gap-2">
      <!-- view toggle -->
      <div class="hidden sm:flex rounded-md border border-gray-200 overflow-hidden text-xs font-medium">
        <button id="btn-split"   onclick="setView('split')"
          class="px-3 py-1.5 bg-gray-900 text-white">Split</button>
        <button id="btn-editor"  onclick="setView('editor')"
          class="px-3 py-1.5 text-gray-500 hover:bg-gray-50 transition-colors">Editor</button>
        <button id="btn-preview" onclick="setView('preview')"
          class="px-3 py-1.5 text-gray-500 hover:bg-gray-50 transition-colors">Preview</button>
      </div>

      <!-- file upload -->
      <label class="cursor-pointer flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 transition-colors px-2 py-1.5 rounded hover:bg-gray-100">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M12 12V4m0 0L8 8m4-4l4 4"/>
        </svg>
        <span class="hidden sm:inline">Open file</span>
        <input type="file" id="file-input" accept=".md,.markdown,.txt" class="hidden" onchange="loadFile(this)" />
      </label>

      <!-- export -->
      <button onclick="exportPdf()" id="btn-export"
        class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-gray-900 text-white text-xs font-medium hover:bg-gray-700 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3"/>
        </svg>
        Export PDF
      </button>
    </div>
  </header>

  <!-- ── status bar ─────────────────────────────────────────────── -->
  <div id="statusbar" class="hidden shrink-0 px-5 py-1 text-xs border-b border-gray-100 bg-amber-50 text-amber-700"></div>

  <!-- ── main split pane ────────────────────────────────────────── -->
  <main id="main" class="flex flex-1 overflow-hidden">

    <!-- editor pane -->
    <div id="pane-editor" class="flex flex-col overflow-hidden" style="width:50%">
      <div class="flex items-center justify-between px-4 py-1.5 border-b border-gray-100 bg-gray-50 shrink-0">
        <span class="text-[11px] font-semibold tracking-widest text-gray-400 select-none">MARKDOWN</span>
        <span id="word-count" class="text-[11px] text-gray-300 select-none"></span>
      </div>
      <textarea id="editor"
        class="flex-1 w-full p-5 font-mono text-sm leading-relaxed text-gray-800 bg-white"
        placeholder="# Hello World&#10;&#10;Start typing Markdown — preview updates live…"
        spellcheck="false"></textarea>
    </div>

    <!-- drag divider -->
    <div id="divider"
      class="w-1 shrink-0 bg-gray-200 hover:bg-blue-400 transition-colors active:bg-blue-500"></div>

    <!-- preview pane -->
    <div id="pane-preview" class="flex flex-col flex-1 overflow-hidden">
      <div class="flex items-center justify-between px-4 py-1.5 border-b border-gray-100 bg-gray-50 shrink-0">
        <span class="text-[11px] font-semibold tracking-widest text-gray-400 select-none">PREVIEW</span>
        <span id="preview-dot" class="text-[11px] text-gray-300 select-none transition-opacity"></span>
      </div>
      <iframe id="preview-frame" sandbox="allow-same-origin"
        srcdoc="<html><body style='padding:2rem;color:#aaa;font-family:sans-serif;font-size:14px'>Start typing to see a live preview…</body></html>">
      </iframe>
    </div>

  </main>

<script>
// ── state ──────────────────────────────────────────────────────────────────
let currentView = 'split';
let previewTimer = null;
let abortCtrl = null;

// ── editor input ──────────────────────────────────────────────────────────
const editor = document.getElementById('editor');
editor.addEventListener('input', () => {
  updateWordCount();
  schedulePreview();
});

function updateWordCount() {
  const words = editor.value.trim().split(/\s+/).filter(Boolean).length;
  document.getElementById('word-count').textContent = words ? words + ' words' : '';
}

// ── live preview ───────────────────────────────────────────────────────────
function schedulePreview() {
  clearTimeout(previewTimer);
  document.getElementById('preview-dot').textContent = '● updating';
  previewTimer = setTimeout(runPreview, 380);
}

async function runPreview() {
  const md = editor.value;
  if (abortCtrl) abortCtrl.abort();
  abortCtrl = new AbortController();

  try {
    const res = await fetch('/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: md }),
      signal: abortCtrl.signal,
    });
    if (!res.ok) return;
    const html = await res.text();
    document.getElementById('preview-frame').srcdoc = html;
    document.getElementById('preview-dot').textContent = '';
  } catch (e) {
    if (e.name !== 'AbortError') {
      document.getElementById('preview-dot').textContent = '⚠ error';
    }
  }
}

// ── export PDF ─────────────────────────────────────────────────────────────
async function exportPdf() {
  const md = editor.value.trim();
  if (!md) { showStatus('Nothing to export — editor is empty.', 'warn'); return; }

  const btn = document.getElementById('btn-export');
  btn.textContent = 'Exporting…';
  btn.disabled = true;
  clearStatus();

  try {
    const res = await fetch('/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: md, filename: 'document' }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      showStatus('Export failed: ' + err.detail, 'error');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: 'document.pdf' }).click();
    URL.revokeObjectURL(url);
  } catch (e) {
    showStatus('Network error: ' + e.message, 'error');
  } finally {
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3"/></svg> Export PDF`;
    btn.disabled = false;
  }
}

// ── file upload ────────────────────────────────────────────────────────────
function loadFile(input) {
  if (!input.files.length) return;
  const reader = new FileReader();
  reader.onload = e => {
    editor.value = e.target.result;
    updateWordCount();
    schedulePreview();
  };
  reader.readAsText(input.files[0]);
  input.value = '';
}

// ── view switching ─────────────────────────────────────────────────────────
function setView(mode) {
  currentView = mode;
  const ep = document.getElementById('pane-editor');
  const pp = document.getElementById('pane-preview');
  const dv = document.getElementById('divider');

  ep.style.display = '';
  pp.style.display = '';
  dv.style.display = '';
  ep.style.width   = '';
  ep.style.flexShrink = '';

  if (mode === 'editor')  { pp.style.display = 'none'; dv.style.display = 'none'; ep.style.width = '100%'; }
  if (mode === 'preview') { ep.style.display = 'none'; dv.style.display = 'none'; }

  ['split', 'editor', 'preview'].forEach(m => {
    const b = document.getElementById('btn-' + m);
    b.className = m === mode
      ? 'px-3 py-1.5 bg-gray-900 text-white text-xs font-medium'
      : 'px-3 py-1.5 text-gray-500 hover:bg-gray-50 transition-colors text-xs font-medium';
  });
}

// ── drag-to-resize ─────────────────────────────────────────────────────────
(function () {
  const divider  = document.getElementById('divider');
  const mainEl   = document.getElementById('main');
  const editorPn = document.getElementById('pane-editor');
  let dragging = false, startX = 0, startW = 0;

  divider.addEventListener('mousedown', e => {
    dragging = true;
    startX   = e.clientX;
    startW   = editorPn.offsetWidth;
    document.body.classList.add('resizing');
    e.preventDefault();
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const total  = mainEl.offsetWidth - divider.offsetWidth;
    const newW   = Math.max(220, Math.min(total - 220, startW + (e.clientX - startX)));
    editorPn.style.width      = newW + 'px';
    editorPn.style.flexShrink = '0';
  });

  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove('resizing');
  });
})();

// ── status bar ─────────────────────────────────────────────────────────────
function showStatus(msg, type) {
  const bar = document.getElementById('statusbar');
  bar.textContent = msg;
  bar.className = 'shrink-0 px-5 py-1 text-xs border-b ' + (
    type === 'error' ? 'bg-red-50 text-red-700 border-red-100' : 'bg-amber-50 text-amber-700 border-amber-100'
  );
  bar.classList.remove('hidden');
}
function clearStatus() {
  document.getElementById('statusbar').classList.add('hidden');
}
</script>
</body>
</html>"""
