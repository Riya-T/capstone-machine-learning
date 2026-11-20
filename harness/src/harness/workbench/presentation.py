"""Render the fixed report's headings, lists and tables as escaped HTML.

Usage: report_html = render_report_text(render_markdown(result))
This is a small renderer for our own report syntax, not arbitrary Markdown or HTML.
"""

from __future__ import annotations

import html
import re


def document(title, body):
    """Wrap already-escaped report markup without external resources."""
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'\">"
        f"<title>{html.escape(title)}</title><style>"
        "body{font:16px/1.6 system-ui;max-width:1150px;margin:2rem auto;padding:1rem;"
        "color:#172b3a;background:#f5f8fb}table{border-collapse:collapse;width:100%;"
        "background:white}th,td{padding:.55rem;text-align:left;border-bottom:1px solid #ccd;}"
        "th{background:#eaf2f8}.scroll{overflow:auto}code{overflow-wrap:anywhere}"
        "</style>" + body + "</html>"
    ).encode()


def inline(text):
    escaped = html.escape(text)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def render_report_text(text):
    lines = text.splitlines()
    rendered, index = [], 0

    def table_start(number):
        return (
            number + 1 < len(lines)
            and lines[number].startswith("|")
            and re.fullmatch(r"\|[-:|\s]+\|", lines[number + 1]) is not None
        )

    def cells(line, tag):
        return (
            "<tr>"
            + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in line.strip("|").split("|"))
            + "</tr>"
        )

    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue
        heading = re.fullmatch(r"(#{1,3}) (.+)", line)
        if heading:
            level, title = len(heading[1]), heading[2]
            rendered.append(f"<h{level}>{inline(title)}</h{level}>")
            index += 1
        elif table_start(index):
            rendered.append('<div class="scroll"><table><thead>')
            rendered.append(cells(line, "th"))
            rendered.append("</thead><tbody>")
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                rendered.append(cells(lines[index], "td"))
                index += 1
            rendered.append("</tbody></table></div>")
        elif line.startswith("- "):
            rendered.append("<ul>")
            while index < len(lines) and lines[index].startswith("- "):
                rendered.append(f"<li>{inline(lines[index][2:])}</li>")
                index += 1
            rendered.append("</ul>")
        else:
            paragraph = [line]
            index += 1
            while (
                index < len(lines)
                and lines[index]
                and not table_start(index)
                and not re.match(r"#{1,3} |^- ", lines[index])
            ):
                paragraph.append(lines[index])
                index += 1
            rendered.append(f"<p>{inline(' '.join(paragraph))}</p>")
    return "\n".join(rendered)
