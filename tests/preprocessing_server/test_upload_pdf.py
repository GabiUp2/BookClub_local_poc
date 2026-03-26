# tests/server/test_upload_pdf.py
"""Tests for PDF upload endpoint."""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import book_club.preprocessing_server.server_main as server_main
from book_club.preprocessing_server.server_main import server


@pytest.fixture
def client():
    """Create a test client for the FastAPI server."""
    return TestClient(server)


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Return minimal valid PDF content for testing."""
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [] /Count 0 >>
endobj
xref
0 3
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
trailer
<< /Size 3 /Root 1 0 R >>
startxref
109
%%EOF"""


@pytest.fixture
def temp_pdf_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary PDF storage directory."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    monkeypatch.setattr(server_main, "PDF_STORAGE_DIR", pdf_dir)
    return pdf_dir


class TestUploadPdfEndpoint:
    """Tests for POST /upload-pdf endpoint."""

    @pytest.mark.test_type("unit")
    def test_upload_valid_pdf_succeeds(
        self,
        client: TestClient,
        sample_pdf_content: bytes,
        temp_pdf_dir: Path,
    ) -> None:
        """Valid PDF upload should return 200 with file metadata."""
        response = client.post(
            "/upload-pdf",
            files={
                "file": (
                    "test_book.pdf",
                    BytesIO(sample_pdf_content),
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["original_filename"] == "test_book.pdf"
        assert data["size_bytes"] == len(sample_pdf_content)
        assert data["message"] == "PDF uploaded successfully."
        assert "filename" in data
        assert data["filename"].endswith("_test_book.pdf")

        # Verify file was actually written
        saved_files = list(temp_pdf_dir.glob("*.pdf"))
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == sample_pdf_content

    @pytest.mark.test_type("unit")
    def test_upload_rejects_non_pdf_content_type(
        self,
        client: TestClient,
        temp_pdf_dir: Path,
    ) -> None:
        """Upload with non-PDF content type should return 400."""
        response = client.post(
            "/upload-pdf",
            files={"file": ("document.txt", BytesIO(b"not a pdf"), "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]

    @pytest.mark.test_type("unit")
    def test_upload_rejects_non_pdf_extension(
        self,
        client: TestClient,
        temp_pdf_dir: Path,
    ) -> None:
        """Upload with non-.pdf extension should return 400."""
        response = client.post(
            "/upload-pdf",
            files={
                "file": ("document.docx", BytesIO(b"fake content"), "application/pdf")
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert ".pdf extension" in data["detail"]

    @pytest.mark.test_type("unit")
    def test_upload_rejects_oversized_file(
        self,
        client: TestClient,
        temp_pdf_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Upload exceeding size limit should return 413."""
        # Set a small limit for testing
        monkeypatch.setattr(server_main, "MAX_PDF_SIZE_MB", 1)

        # Create content larger than 1MB
        large_content = b"%PDF-1.4\n" + b"x" * (2 * 1024 * 1024)

        response = client.post(
            "/upload-pdf",
            files={"file": ("big_book.pdf", BytesIO(large_content), "application/pdf")},
        )

        assert response.status_code == 413
        data = response.json()
        assert "too large" in data["detail"].lower()

    @pytest.mark.test_type("unit")
    def test_upload_sanitises_filename(
        self,
        client: TestClient,
        sample_pdf_content: bytes,
        temp_pdf_dir: Path,
    ) -> None:
        """Filenames with special characters should be sanitised."""
        response = client.post(
            "/upload-pdf",
            files={
                "file": (
                    "My Book (2024) [v1].pdf",
                    BytesIO(sample_pdf_content),
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Special chars should be replaced with underscores
        assert "(" not in data["filename"]
        assert "[" not in data["filename"]

    @pytest.mark.test_type("unit")
    def test_upload_generates_unique_filenames(
        self,
        client: TestClient,
        sample_pdf_content: bytes,
        temp_pdf_dir: Path,
    ) -> None:
        """Multiple uploads of same file should create unique filenames."""
        filenames = []
        for _ in range(3):
            response = client.post(
                "/upload-pdf",
                files={
                    "file": (
                        "same_book.pdf",
                        BytesIO(sample_pdf_content),
                        "application/pdf",
                    )
                },
            )
            assert response.status_code == 200
            filenames.append(response.json()["filename"])

        # All filenames should be unique
        assert len(set(filenames)) == 3

    @pytest.mark.test_type("unit")
    def test_upload_handles_storage_error(
        self,
        client: TestClient,
        sample_pdf_content: bytes,
        temp_pdf_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Storage write failure should return 500."""

        # Make the write operation fail
        def mock_write_bytes(self, data):
            raise OSError("Disk full")

        monkeypatch.setattr(Path, "write_bytes", mock_write_bytes)

        response = client.post(
            "/upload-pdf",
            files={
                "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to save" in data["detail"]

    @pytest.mark.test_type("unit")
    def test_upload_creates_storage_directory_if_missing(
        self,
        client: TestClient,
        sample_pdf_content: bytes,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Upload should create storage directory if it doesn't exist."""
        new_dir = tmp_path / "new_pdfs_dir"
        assert not new_dir.exists()

        monkeypatch.setattr(server_main, "PDF_STORAGE_DIR", new_dir)

        response = client.post(
            "/upload-pdf",
            files={
                "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")
            },
        )

        assert response.status_code == 200
        assert new_dir.exists()
        assert len(list(new_dir.glob("*.pdf"))) == 1
