from uuid import uuid4

from app.restaurants.menu_items.csv.dtos import CsvUploadUrlResponseDTO
from app.settings import CSV_UPLOAD_BUCKET_NAME
from app.utils import generate_signed_upload_url


class CsvUploadService:
    """Handles CSV menu item upload operations."""

    def generate_upload_url(
        self, restaurant_id: str, content_type: str
    ) -> CsvUploadUrlResponseDTO:
        """Generate a signed URL for uploading a menu items CSV file."""
        upload_id = uuid4().hex
        object_path = f"{restaurant_id}/{upload_id}"
        upload_url = generate_signed_upload_url(
            object_path, content_type, bucket_name=CSV_UPLOAD_BUCKET_NAME
        )
        return CsvUploadUrlResponseDTO(upload_url=upload_url, upload_id=upload_id)
