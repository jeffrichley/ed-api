from typer.testing import CliRunner
from ed_api.cli.main import app
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown

runner = CliRunner()


class TestContentCLI:
    def test_to_xml(self):
        result = runner.invoke(app, ["content", "to-xml", "Hello **world**", "--json"])
        assert result.exit_code == 0
        assert "document" in result.stdout

    def test_to_markdown(self):
        xml = '<document version="2.0"><paragraph>Hello</paragraph></document>'
        result = runner.invoke(app, ["content", "to-markdown", xml, "--json"])
        assert result.exit_code == 0
        assert "Hello" in result.stdout


class TestCLIHelp:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ed-api" in result.stdout.lower() or "edstem" in result.stdout.lower()

    def test_threads_help(self):
        result = runner.invoke(app, ["threads", "--help"])
        assert result.exit_code == 0

    def test_comments_help(self):
        result = runner.invoke(app, ["comments", "--help"])
        assert result.exit_code == 0
