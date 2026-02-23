import re

import mistune
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from weasyprint import CSS, HTML

from .styles import build_full_css

# WeasyPrint has no reliable rendering for <input> form elements, so we swap
# them out for Unicode ballot boxes before the HTML ever reaches the PDF engine.
_RE_PAGE_AT_RULE = re.compile(r"@page\s*\{[^{}]*\}", re.DOTALL)

_RE_CHECKED = re.compile(
    r'<input class="task-list-item-checkbox" type="checkbox" disabled checked\s*/?>',
    re.IGNORECASE,
)
_RE_UNCHECKED = re.compile(
    r'<input class="task-list-item-checkbox" type="checkbox" disabled\s*/?>',
    re.IGNORECASE,
)


def _replace_checkboxes(html: str) -> str:
    html = _RE_CHECKED.sub(
        '<span class="task-checkbox task-checked">&#x2611;</span>', html
    )
    html = _RE_UNCHECKED.sub(
        '<span class="task-checkbox">&#x2610;</span>', html
    )
    return html

_FORMATTER = HtmlFormatter(style="friendly", cssclass="highlight", nowrap=False)


class _HighlightRenderer(mistune.HTMLRenderer):
    """mistune renderer that delegates fenced code blocks to Pygments."""

    def block_code(self, code: str, **attrs: object) -> str:
        info = (attrs.get("info") or "").strip()
        lang = info.split(None, 1)[0] if info else ""
        try:
            lexer = get_lexer_by_name(lang, stripall=True) if lang else TextLexer()
        except Exception:
            lexer = TextLexer()
        return highlight(code, lexer, _FORMATTER)


_md = mistune.create_markdown(
    renderer=_HighlightRenderer(escape=False),
    plugins=["table", "strikethrough", "task_lists", "url", "def_list"],
)

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
</head>
<body class="markdown-body">
{body}
</body>
</html>
"""


def markdown_to_html(source: str) -> str:
    """Return a complete browser-renderable HTML page for the live preview iframe."""
    body = _replace_checkboxes(_md(source))
    # @page at-rules are PDF-only; strip them so the browser preview looks clean
    preview_css = _RE_PAGE_AT_RULE.sub("", build_full_css())
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="utf-8"/>'
        f"<style>{preview_css}</style>"
        "</head>"
        '<body style="padding:2rem 2.5rem;max-width:860px;margin:0 auto">'
        f"{body}"
        "</body></html>"
    )


def markdown_to_pdf(source: str, title: str = "document") -> bytes:
    """Convert a Markdown string to PDF bytes using GitHub-flavoured styling."""
    body = _replace_checkboxes(_md(source))
    html_content = _HTML_TEMPLATE.format(title=title, body=body)

    css = CSS(string=build_full_css())
    pdf_bytes = HTML(string=html_content, base_url=None).write_pdf(stylesheets=[css])
    return pdf_bytes
