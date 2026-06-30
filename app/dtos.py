from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseDTO(BaseModel):
    """Base DTO to automatically apply camelCase support."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CurrencyDTO(BaseDTO):
    """Represents a currency with its code and symbol."""

    code: str
    symbol: str


class UploadUrlRequestDTO(BaseDTO):
    """DTO for requesting signed upload URL."""

    file_name: str
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    file_size: int = Field(gt=0)
