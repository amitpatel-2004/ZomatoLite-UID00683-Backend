from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseDTO(BaseModel):
    """Base DTO to automatically apply camelCase support."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
