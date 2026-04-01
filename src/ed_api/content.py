"""Markdown ↔ Ed XML content conversion.

EdStem uses a custom XML format for post bodies. This module converts
between standard markdown and Ed's XML format.
"""

import re
from xml.sax.saxutils import escape as xml_escape

from bs4 import BeautifulSoup


def markdown_to_ed_xml(md: str) -> str:
    """Convert markdown text to Ed's XML document format."""
    lines = md.split("\n")
    elements: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block (fenced)
        if line.strip().startswith("```"):
            lang_match = re.match(r"^```(\w*)", line.strip())
            lang = lang_match.group(1) if lang_match else ""
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code = "\n".join(code_lines)
            if lang:
                elements.append(f'<snippet language="{lang}" runnable="false">{xml_escape(code)}</snippet>')
            else:
                elements.append(f"<pre>{xml_escape(code)}</pre>")
            continue

        # Heading
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = _inline_to_xml(heading_match.group(2))
            elements.append(f'<heading level="{level}">{text}</heading>')
            i += 1
            continue

        # Unordered list
        if re.match(r"^[-*+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i]):
                item_text = re.sub(r"^[-*+]\s+", "", lines[i])
                items.append(f"<list-item><paragraph>{_inline_to_xml(item_text)}</paragraph></list-item>")
                i += 1
            elements.append(f'<list style="bullet">{"".join(items)}</list>')
            continue

        # Ordered list
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item_text = re.sub(r"^\d+\.\s+", "", lines[i])
                items.append(f"<list-item><paragraph>{_inline_to_xml(item_text)}</paragraph></list-item>")
                i += 1
            elements.append(f'<list style="number">{"".join(items)}</list>')
            continue

        # Blank line — skip
        if not line.strip():
            i += 1
            continue

        # Regular paragraph
        text = _inline_to_xml(line)
        elements.append(f"<paragraph>{text}</paragraph>")
        i += 1

    return f'<document version="2.0">{"".join(elements)}</document>'


def _inline_to_xml(text: str) -> str:
    """Convert inline markdown formatting to Ed XML tags."""
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<bold>\1</bold>", text)
    text = re.sub(r"__(.+?)__", r"<bold>\1</bold>", text)
    # Italic: *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<italic>\1</italic>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<italic>\1</italic>", text)
    # Inline code: `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2">\1</link>', text)
    return text


def ed_xml_to_markdown(xml: str) -> str:
    """Convert Ed's XML document format to markdown."""
    # Try parsers in order of preference
    soup = None
    for parser in ("lxml-xml", "xml", "html.parser"):
        try:
            soup = BeautifulSoup(xml, parser)
            break
        except Exception:
            continue

    if soup is None:
        return xml  # fallback: return raw

    doc = soup.find("document")
    if not doc:
        doc = soup
    return _node_to_markdown(doc).strip()


def _node_to_markdown(node) -> str:
    """Recursively convert an XML node to markdown."""
    if node.string is not None and node.name is None:
        return str(node.string)

    parts = []
    for child in node.children:
        if child.name is None:
            parts.append(str(child))
            continue

        tag = child.name.lower() if child.name else ""

        if tag == "document":
            parts.append(_node_to_markdown(child))
        elif tag == "heading":
            level = int(child.get("level", 1))
            text = _node_to_markdown(child)
            parts.append(f"\n{'#' * level} {text}\n")
        elif tag == "paragraph":
            text = _node_to_markdown(child)
            parts.append(f"\n{text}\n")
        elif tag == "bold":
            parts.append(f"**{_node_to_markdown(child)}**")
        elif tag == "italic":
            parts.append(f"*{_node_to_markdown(child)}*")
        elif tag == "underline":
            parts.append(f"__{_node_to_markdown(child)}__")
        elif tag == "code":
            parts.append(f"`{_node_to_markdown(child)}`")
        elif tag == "pre":
            parts.append(f"\n```\n{_node_to_markdown(child)}\n```\n")
        elif tag == "snippet":
            lang = child.get("language", "")
            parts.append(f"\n```{lang}\n{_node_to_markdown(child)}\n```\n")
        elif tag == "link":
            href = child.get("href", "")
            text = _node_to_markdown(child)
            parts.append(f"[{text}]({href})")
        elif tag == "list":
            style = child.get("style", "bullet")
            items = child.find_all("list-item", recursive=False)
            for idx, item in enumerate(items, 1):
                item_text = _node_to_markdown(item).strip()
                if style == "number":
                    parts.append(f"\n{idx}. {item_text}")
                else:
                    parts.append(f"\n- {item_text}")
            parts.append("\n")
        elif tag == "list-item":
            parts.append(_node_to_markdown(child))
        elif tag == "math":
            parts.append(f"${_node_to_markdown(child)}$")
        elif tag == "callout":
            text = _node_to_markdown(child)
            ctype = child.get("type", "info")
            parts.append(f"\n> **{ctype.upper()}:** {text}\n")
        elif tag == "spoiler":
            parts.append(f"\n||{_node_to_markdown(child)}||\n")
        elif tag == "image":
            src = child.get("src", "")
            parts.append(f"![image]({src})")
        elif tag == "figure":
            parts.append(_node_to_markdown(child))
        elif tag == "file":
            url = child.get("url", "")
            parts.append(f"[file]({url})")
        else:
            parts.append(_node_to_markdown(child))

    return "".join(parts)
