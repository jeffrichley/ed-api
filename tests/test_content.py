from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown


class TestMarkdownToEdXml:
    def test_simple_paragraph(self):
        xml = markdown_to_ed_xml("Hello world")
        assert '<document version="2.0">' in xml
        assert "<paragraph>" in xml
        assert "Hello world" in xml

    def test_heading(self):
        xml = markdown_to_ed_xml("## My Heading")
        assert '<heading level="2">' in xml
        assert "My Heading" in xml

    def test_bold(self):
        xml = markdown_to_ed_xml("Some **bold** text")
        assert "<bold>" in xml
        assert "bold" in xml

    def test_italic(self):
        xml = markdown_to_ed_xml("Some *italic* text")
        assert "<italic>" in xml

    def test_code_inline(self):
        xml = markdown_to_ed_xml("Use `print()` function")
        assert "<code>" in xml
        assert "print()" in xml

    def test_code_block(self):
        xml = markdown_to_ed_xml("```python\nprint('hello')\n```")
        assert "<snippet" in xml or "<pre>" in xml

    def test_link(self):
        xml = markdown_to_ed_xml("[Click here](https://example.com)")
        assert '<link href="https://example.com">' in xml

    def test_list(self):
        xml = markdown_to_ed_xml("- Item 1\n- Item 2")
        assert '<list style="bullet">' in xml
        assert "<list-item>" in xml

    def test_numbered_list(self):
        xml = markdown_to_ed_xml("1. First\n2. Second")
        assert '<list style="number">' in xml


class TestEdXmlToMarkdown:
    def test_simple_paragraph(self):
        xml = '<document version="2.0"><paragraph>Hello world</paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "Hello world" in md

    def test_heading(self):
        xml = '<document version="2.0"><heading level="2">My Heading</heading></document>'
        md = ed_xml_to_markdown(xml)
        assert "## My Heading" in md

    def test_bold(self):
        xml = '<document version="2.0"><paragraph>Some <bold>bold</bold> text</paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "**bold**" in md

    def test_code_inline(self):
        xml = '<document version="2.0"><paragraph>Use <code>print()</code></paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "`print()`" in md

    def test_link(self):
        xml = '<document version="2.0"><paragraph><link href="https://example.com">Click</link></paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "[Click](https://example.com)" in md

    def test_roundtrip_simple(self):
        original = "Hello **bold** and *italic* text"
        xml = markdown_to_ed_xml(original)
        md = ed_xml_to_markdown(xml)
        assert "bold" in md
        assert "italic" in md
