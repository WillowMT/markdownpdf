from pygments.formatters import HtmlFormatter

# Pygments syntax highlighting CSS (friendly style — clean on white)
PYGMENTS_CSS = HtmlFormatter(style="friendly", cssclass="highlight").get_style_defs(
    ".highlight"
)

GITHUB_CSS = """
@page {
  size: A4;
  margin: 2cm 2.5cm;
  @bottom-center {
    content: counter(page) " / " counter(pages);
    font-size: 10px;
    color: #57606a;
    font-family: -apple-system, "Liberation Sans", Helvetica, Arial, sans-serif;
  }
}

* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Liberation Sans",
    Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: #24292f;
  background: #ffffff;
  word-wrap: break-word;
}

a {
  color: #0969da;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

h1, h2, h3, h4, h5, h6 {
  margin-top: 32px;
  margin-bottom: 20px;
  font-weight: 600;
  line-height: 1.25;
  page-break-after: avoid;
}

h1 {
  font-size: 2em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #d0d7de;
}

h2 {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #d0d7de;
}

h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: 0.875em; }
h6 { font-size: 0.85em; color: #57606a; }

p {
  margin-top: 0;
  margin-bottom: 20px;
}

blockquote {
  margin: 0 0 20px;
  padding: 0 1em;
  color: #57606a;
  border-left: 0.25em solid #d0d7de;
}

blockquote > :first-child { margin-top: 0; }
blockquote > :last-child  { margin-bottom: 0; }

/* Inline code */
code {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
    "Liberation Mono", monospace;
  font-size: 85%;
  padding: 0.2em 0.4em;
  background: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
}

/* Code blocks — wraps pygments .highlight div */
pre {
  margin-top: 0;
  margin-bottom: 20px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background: #f6f8fa;
  border-radius: 6px;
  page-break-inside: avoid;
}

pre code,
.highlight code {
  display: inline;
  padding: 0;
  margin: 0;
  background: transparent;
  border: 0;
  font-size: 100%;
  word-wrap: normal;
}

.highlight {
  background: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 20px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
    "Liberation Mono", monospace;
}

.highlight pre {
  margin: 0;
  padding: 0;
  background: transparent;
  border-radius: 0;
}

table {
  border-spacing: 0;
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 20px;
  overflow: auto;
  display: table;
  page-break-inside: avoid;
}

table th {
  font-weight: 600;
}

table th,
table td {
  padding: 6px 13px;
  border: 1px solid #d0d7de;
}

table tr {
  background-color: #ffffff;
  border-top: 1px solid hsla(210, 18%, 87%, 1);
}

table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

hr {
  height: 1px;
  padding: 0;
  margin: 32px 0;
  background-color: #d0d7de;
  border: 0;
}

ul,
ol {
  margin-top: 0;
  margin-bottom: 20px;
  padding-left: 2em;
}

ul ul,
ul ol,
ol ol,
ol ul {
  margin-top: 0;
  margin-bottom: 0;
}

li {
  word-wrap: break-word;
}

li > p {
  margin-top: 16px;
}

li + li {
  margin-top: 0.25em;
}

img {
  max-width: 100%;
  box-sizing: content-box;
}

/* GFM task lists */
ul:has(.task-list-item) {
  padding-left: 0.5em;
  list-style: none;
}

.task-list-item {
  list-style-type: none;
  display: flex;
  align-items: baseline;
  gap: 0.45em;
}

.task-checkbox {
  flex-shrink: 0;
  font-size: 1.05em;
  line-height: 1.5;
  color: #57606a;
}

.task-checked {
  color: #1a7f37;
}

/* Definition lists */
dl {
  padding: 0;
}

dl dt {
  padding: 0;
  margin-top: 16px;
  font-size: 1em;
  font-style: italic;
  font-weight: 600;
}

dl dd {
  padding: 0 16px;
  margin-bottom: 16px;
}
"""


def build_full_css() -> str:
    return GITHUB_CSS + "\n" + PYGMENTS_CSS
