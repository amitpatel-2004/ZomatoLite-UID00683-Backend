from typing import Literal

from pydantic import Field

from app.dtos import BaseDTO


class CsvUploadUrlRequestDTO(BaseDTO):
    content_type: Literal["text/csv"]
    file_size: int = Field(gt=0)


class CsvUploadUrlResponseDTO(BaseDTO):
    upload_url: str
    upload_id: str
