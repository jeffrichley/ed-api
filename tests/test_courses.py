from unittest.mock import MagicMock
from ed_api.resources.courses import CoursesResource


class TestCoursesResource:
    def test_list(self, user_info_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = user_info_response
        mock_http.get.return_value = mock_resp

        resource = CoursesResource(mock_http)
        result = resource.list()

        assert len(result) == 1
        assert result[0].course.code == "CS7646"

    def test_users(self):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "users": [
                {"id": 1, "name": "Alice", "email": "a@b.com", "role": "user", "course_role": "staff"},
                {"id": 2, "name": "Bob", "email": "b@b.com", "role": "user", "course_role": "student"},
            ]
        }
        mock_http.get.return_value = mock_resp

        resource = CoursesResource(mock_http)
        all_users = resource.users(54321)
        assert len(all_users) == 2

        staff = resource.users(54321, role="staff")
        assert len(staff) == 1
        assert staff[0].name == "Alice"
