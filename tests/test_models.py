from datetime import datetime
from ed_api.models import (
    UserSummary, UserInfo, CourseUser, Course, CourseEnrollment,
    Thread, ThreadDetail, Comment,
    parse_thread, parse_thread_detail, parse_comment, parse_user_info,
)


class TestUserSummary:
    def test_create(self):
        u = UserSummary(id=1, name="Alice", role="staff")
        assert u.name == "Alice"
        assert u.role == "staff"

    def test_is_staff(self):
        assert UserSummary(id=1, name="A", role="staff").is_staff is True
        assert UserSummary(id=1, name="A", role="admin").is_staff is True
        assert UserSummary(id=1, name="A", role="student").is_staff is False


class TestThread:
    def test_parse_from_api(self, thread_list_response):
        raw = thread_list_response["threads"][0]
        thread = parse_thread(raw)
        assert thread.id == 100
        assert thread.number == 1
        assert thread.title == "get_data() returns NaN"
        assert thread.type == "question"
        assert thread.category == "Project 1"
        assert thread.is_answered is True
        assert isinstance(thread.author, UserSummary)
        assert isinstance(thread.created_at, datetime)


class TestThreadDetail:
    def test_parse_with_comments(self, thread_detail_response):
        raw = thread_detail_response
        thread = parse_thread_detail(raw)
        assert isinstance(thread, ThreadDetail)
        assert len(thread.comments) == 2  # 1 answer + 1 comment
        assert thread.comments[0].is_endorsed is True  # the answer

    def test_is_unanswered(self, thread_detail_response):
        raw = thread_detail_response
        thread = parse_thread_detail(raw)
        assert thread.is_unanswered is False

    def test_has_staff_response(self, thread_detail_response):
        raw = thread_detail_response
        users = {u["id"]: u for u in raw["users"]}
        thread = parse_thread_detail(raw)
        assert thread.has_staff_response is True


class TestComment:
    def test_parse_from_api(self, comment_response):
        raw = comment_response["comment"]
        comment = parse_comment(raw)
        assert comment.id == 300
        assert comment.thread_id == 100
        assert comment.parent_id is None


class TestUserInfo:
    def test_parse_user_info(self, user_info_response):
        info = parse_user_info(user_info_response)
        assert info.user.id == 12345
        assert info.user.name == "Test User"
        assert len(info.courses) == 1
        assert info.courses[0].course.code == "CS7646"
        assert info.courses[0].role == "admin"
