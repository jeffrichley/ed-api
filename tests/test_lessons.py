from unittest.mock import MagicMock

from ed_api.models import Lesson, Module, Slide, parse_lesson, parse_module, parse_slide
from ed_api.resources.lessons import LessonsResource


class TestParseModels:
    def test_parse_slide(self):
        raw = {
            "id": 9001,
            "lesson_id": 5001,
            "course_id": 54321,
            "type": "video",
            "title": "My Video",
            "index": 0,
            "is_hidden": False,
            "content": "",
            "video_url": "https://example.com/video.mp4",
            "file_url": None,
            "url": None,
            "created_at": "2026-01-15T10:00:00.000Z",
        }
        slide = parse_slide(raw)
        assert isinstance(slide, Slide)
        assert slide.id == 9001
        assert slide.type == "video"
        assert slide.video_url == "https://example.com/video.mp4"
        assert slide.created_at is not None

    def test_parse_lesson(self, lesson_detail_response):
        raw = lesson_detail_response["lesson"]
        lesson = parse_lesson(raw)
        assert isinstance(lesson, Lesson)
        assert lesson.id == 5001
        assert lesson.title == "Lesson 01: Reading Data"
        assert len(lesson.slides) == 2
        assert lesson.slides[0].type == "document"
        assert lesson.slides[1].type == "video"

    def test_parse_module(self):
        raw = {"id": 100, "name": "Part 1: Data Access", "course_id": 54321}
        module = parse_module(raw)
        assert isinstance(module, Module)
        assert module.id == 100
        assert module.name == "Part 1: Data Access"

    def test_parse_lesson_no_slides(self):
        raw = {
            "id": 5002,
            "course_id": 54321,
            "module_id": None,
            "title": "Empty Lesson",
            "lesson_number": 2,
            "is_hidden": False,
            "is_unlisted": False,
            "created_at": None,
            "available_at": None,
            "due_at": None,
        }
        lesson = parse_lesson(raw)
        assert lesson.slides == []
        assert lesson.module_id is None
        assert lesson.created_at is None


class TestLessonsResource:
    def _make_resource(self):
        mock_http = MagicMock()
        return LessonsResource(mock_http), mock_http

    def test_list(self, lessons_list_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = lessons_list_response
        mock_http.get.return_value = mock_resp

        lessons, modules = resource.list(54321)
        assert len(lessons) == 1
        assert isinstance(lessons[0], Lesson)
        assert lessons[0].title == "Lesson 01: Reading Data"
        assert len(modules) == 1
        assert isinstance(modules[0], Module)
        assert modules[0].name == "Part 1: Data Access"
        mock_http.get.assert_called_once_with("courses/54321/lessons")

    def test_get(self, lesson_detail_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = lesson_detail_response
        mock_http.get.return_value = mock_resp

        lesson = resource.get(5001)
        assert isinstance(lesson, Lesson)
        assert lesson.title == "Lesson 01: Reading Data"
        assert len(lesson.slides) == 2
        mock_http.get.assert_called_once_with("lessons/5001")

    def test_get_slide(self):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "slide": {
                "id": 9002,
                "lesson_id": 5001,
                "course_id": 54321,
                "type": "video",
                "title": "Reading Stock Data",
                "index": 1,
                "is_hidden": False,
                "content": "",
                "video_url": "https://cfvod.kaltura.com/video.mp4",
                "file_url": None,
                "url": None,
                "created_at": "2026-01-15T10:00:00.000Z",
            }
        }
        mock_http.get.return_value = mock_resp

        slide = resource.get_slide(9002)
        assert isinstance(slide, Slide)
        assert slide.type == "video"
        assert slide.video_url == "https://cfvod.kaltura.com/video.mp4"
        mock_http.get.assert_called_once_with("lessons/slides/9002")

    def test_video_slides(self, lessons_list_response, lesson_detail_response):
        resource, mock_http = self._make_resource()

        list_resp = MagicMock()
        list_resp.json.return_value = lessons_list_response
        detail_resp = MagicMock()
        detail_resp.json.return_value = lesson_detail_response

        mock_http.get.side_effect = [list_resp, detail_resp]

        results = resource.video_slides(54321)
        assert len(results) == 1
        lesson, slide = results[0]
        assert slide.type == "video"
        assert slide.title == "Reading Stock Data"
        assert lesson.title == "Lesson 01: Reading Data"


class TestLessonsCLI:
    def test_list_command(self, lessons_list_response, monkeypatch):
        from typer.testing import CliRunner
        from ed_api.cli.lessons import app

        mock_client = MagicMock()
        mock_client.lessons.list.return_value = (
            [parse_lesson(l) for l in lessons_list_response["lessons"]],
            [parse_module(m) for m in lessons_list_response["modules"]],
        )
        monkeypatch.setattr("ed_api.cli.lessons.EdClient", lambda: mock_client)

        runner = CliRunner()
        result = runner.invoke(app, ["list", "54321", "--json"])
        assert result.exit_code == 0
        data = __import__("json").loads(result.stdout)
        assert len(data["lessons"]) == 1
        assert data["lessons"][0]["title"] == "Lesson 01: Reading Data"

    def test_videos_command(self, lesson_detail_response, monkeypatch):
        from typer.testing import CliRunner
        from ed_api.cli.lessons import app

        lesson = parse_lesson(lesson_detail_response["lesson"])
        video_slide = [s for s in lesson.slides if s.type == "video"][0]
        mock_client = MagicMock()
        mock_client.lessons.video_slides.return_value = [(lesson, video_slide)]
        monkeypatch.setattr("ed_api.cli.lessons.EdClient", lambda: mock_client)

        runner = CliRunner()
        result = runner.invoke(app, ["videos", "54321", "--json"])
        assert result.exit_code == 0
        data = __import__("json").loads(result.stdout)
        assert len(data) == 1
        assert data[0]["slide_title"] == "Reading Stock Data"
        assert "kaltura" in data[0]["video_url"]
