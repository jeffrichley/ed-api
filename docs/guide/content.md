# Content Conversion

EdStem stores thread and comment bodies as a custom XML format. ed-api provides `markdown_to_ed_xml()` and `ed_xml_to_markdown()` to convert between the two.

All `create()`, `edit()`, `post()`, and `reply()` methods call `markdown_to_ed_xml()` automatically — you write Markdown, the library handles the conversion.

## Markdown to Ed XML

```python
from ed_api.content import markdown_to_ed_xml

md = """
# Hello World

This is a **bold** statement with *italic* text and `inline code`.

Here is a code block:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

And a list:

- Item one
- Item two
- Item three
"""

xml = markdown_to_ed_xml(md)
print(xml)
```

Output:

```xml
<document version="2.0">
  <heading level="1">Hello World</heading>
  <paragraph>This is a <bold>bold</bold> statement with <italic>italic</italic> text and <code>inline code</code>.</paragraph>
  <snippet language="python" runnable="false">def greet(name: str) -&gt; str:
    return f"Hello, {name}!"</snippet>
  <list style="bullet">
    <list-item><paragraph>Item one</paragraph></list-item>
    <list-item><paragraph>Item two</paragraph></list-item>
    <list-item><paragraph>Item three</paragraph></list-item>
  </list>
</document>
```

## Ed XML to Markdown

```python
from ed_api.content import ed_xml_to_markdown

xml = '<document version="2.0"><paragraph>Hello <bold>world</bold>!</paragraph></document>'
md = ed_xml_to_markdown(xml)
print(md)
# Hello **world**!
```

Useful for rendering thread content in terminal output or processing thread bodies programmatically.

## Supported Markdown syntax

### Headings

```markdown
# H1
## H2
### H3
#### H4
```

Converted to `<heading level="1">` through `<heading level="4">`.

### Inline formatting

| Markdown | Ed XML |
|---|---|
| `**bold**` or `__bold__` | `<bold>bold</bold>` |
| `*italic*` or `_italic_` | `<italic>italic</italic>` |
| `` `code` `` | `<code>code</code>` |
| `[text](url)` | `<link href="url">text</link>` |

### Code blocks

Fenced code blocks with a language hint become `<snippet>` elements:

````markdown
```python
x = 42
```
````

```xml
<snippet language="python" runnable="false">x = 42</snippet>
```

Fenced code blocks without a language hint become `<pre>` elements:

````markdown
```
plain text block
```
````

```xml
<pre>plain text block</pre>
```

### Lists

Unordered lists:

```markdown
- First item
- Second item
* Third item (asterisk also works)
```

```xml
<list style="bullet">
  <list-item><paragraph>First item</paragraph></list-item>
  <list-item><paragraph>Second item</paragraph></list-item>
  <list-item><paragraph>Third item</paragraph></list-item>
</list>
```

Ordered lists:

```markdown
1. Step one
2. Step two
3. Step three
```

```xml
<list style="number">
  <list-item><paragraph>Step one</paragraph></list-item>
  ...
</list>
```

### Paragraphs

Any non-blank line that does not match another pattern becomes a `<paragraph>` element. Inline formatting is applied within paragraphs.

## Supported Ed XML elements (for `ed_xml_to_markdown`)

When converting from Ed XML to Markdown, the following elements are handled:

| Ed XML tag | Markdown output |
|---|---|
| `<heading level="N">` | `# ...` (N hashes) |
| `<paragraph>` | Plain paragraph |
| `<bold>` | `**...**` |
| `<italic>` | `*...*` |
| `<underline>` | `__...__` |
| `<code>` | `` `...` `` |
| `<pre>` | ` ``` ... ``` ` |
| `<snippet language="x">` | ` ```x ... ``` ` |
| `<link href="url">` | `[text](url)` |
| `<list style="bullet">` | `- item` per list-item |
| `<list style="number">` | `1. item` per list-item |
| `<math>` | `$...$` |
| `<callout type="x">` | `> **X:** ...` |
| `<image src="url">` | `![image](url)` |
| `<file url="url">` | `[file](url)` |

## CLI usage

Convert Markdown to Ed XML:

```bash
ed-api content to-xml "Hello **world**!"
# <document version="2.0"><paragraph>Hello <bold>world</bold>!</paragraph></document>

ed-api content to-xml "Hello **world**!" --json
# {"xml": "<document version=\"2.0\">..."}
```

Convert Ed XML to Markdown:

```bash
ed-api content to-markdown '<document version="2.0"><paragraph>Hello <bold>world</bold>!</paragraph></document>'
# Hello **world**!

ed-api content to-markdown '...' --json
# {"markdown": "Hello **world**!"}
```

## Advanced: processing thread content

```python
from ed_api import EdClient
from ed_api.content import ed_xml_to_markdown

client = EdClient()

# Fetch all threads and extract text for analysis
for thread in client.threads.list_all(course_id=12345):
    detail = client.threads.get(thread.id)
    body_md = ed_xml_to_markdown(detail.content)

    # Now you have plain Markdown — search, summarize, etc.
    if "error" in body_md.lower():
        print(f"#{thread.number}: {thread.title}")
        print(body_md[:200])
```
