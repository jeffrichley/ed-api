from unittest.mock import MagicMock
from ed_api.resources.files import FilesResource


class TestFilesResource:
    def test_upload(self, file_upload_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = file_upload_response
        mock_http.upload.return_value = mock_resp

        resource = FilesResource(mock_http, region="us")
        url = resource.upload("test.png", b"fake-png-bytes", "image/png")

        assert "abc123def456" in url
        mock_http.upload.assert_called_once()

    def test_upload_from_path(self, tmp_path, file_upload_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = file_upload_response
        mock_http.upload.return_value = mock_resp

        test_file = tmp_path / "screenshot.png"
        test_file.write_bytes(b"fake-png-bytes")

        resource = FilesResource(mock_http, region="us")
        url = resource.upload_from_path(test_file)

        assert "abc123def456" in url
