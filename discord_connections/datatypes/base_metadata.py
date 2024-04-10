import json
import re
from datetime import datetime

from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict

from field_types import IntGe, DtGe, BoolEq


class MetadataField(BaseModel):
    key: str
    value: Optional[Any] = None
    name: str
    name_localizations: Optional[dict] = Field(default=None)
    description: str
    description_localizations: Optional[dict] = Field(default=None)

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: Any):
        pattern = re.compile(r'[a-z0-9_]*')
        if not pattern.fullmatch(v):
            raise ValueError("Only a-z, 0-9, or _ characters can be used as key of metadata field")
        if not 1 <= len(v) <= 50:
            raise ValueError("Key of metadata field must be 1-50 characters long")

        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Any):
        if not 1 <= len(v) <= 100:
            raise ValueError("Name of metadata field must be 1-100 characters long")

        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Any):
        if not 1 <= len(v) <= 100:
            raise ValueError("Description of metadata field must be 1-200 characters long")

        return v

    # TODO validate localisations


class BaseMetadata(BaseModel):
    platform_name: str = Field(...)
    platform_username: str = Field(default=None)

    model_config = ConfigDict(ser_json_timedelta='iso8601')

    @classmethod
    def to_schema(cls) -> json:
        fields = []
        for field_name, field_info in cls.model_fields.items():
            if isinstance(field_info.default, MetadataField):
                fields.append({
                    "type": field_info.annotation.type,
                    **field_info.default.model_dump()
                })

        return json.dumps(fields)


if __name__ == "__main__":
    class ActualMetadata(BaseMetadata):
        platform_name: str = "actual"
        concrete_field: IntGe = MetadataField(
            key='cf1',
            name='concrete_field_1',
            description='concrete_field_1_description'
        )
        other_concrete_field: DtGe = MetadataField(
            key='cf2',
            name='concrete_field_2',
            description='concrete_field_2_description'
        )
        another_concrete_field: BoolEq = MetadataField(
            key='cf3',
            name='concrete_field_3',
            description='concrete_field_3_description'
        )

    # print(ActualMetadata.to_schema())

    a = ActualMetadata(
        platform_name="asd",
        concrete_field=12,
        other_concrete_field=datetime.now(),
    )

    print(a.concrete_field.value)

    # print(a.another_concrete_field)

    # print(a.model_dump_json(exclude_none=True))
