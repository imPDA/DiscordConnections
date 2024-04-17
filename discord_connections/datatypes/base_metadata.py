import json
import re

from typing import Optional, Any, TypeVar, Generic, get_args, Type, Self

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

from .field_types import IntGe, DtGe, BoolEq, IntLe, DtLe, IntEq, IntNe, BoolNe
from .exceptions import TooManyFieldsException

FieldType = TypeVar('FieldType', IntLe, IntGe, IntEq, IntNe, DtLe, DtGe, BoolEq, BoolNe)


class MetadataField(BaseModel, Generic[FieldType]):
    key: str
    value: Optional[FieldType] = Field(default=None)
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


class BaseMetadataModel(BaseModel):
    platform_name: str = Field(...)
    platform_username: str = Field(default=None)

    model_config = ConfigDict(
        ser_json_timedelta='iso8601',
        arbitrary_types_allowed=True
    )

    @model_validator(mode='before')
    @classmethod
    def rewrite_values(cls, data: Any):
        # 1) Actual check for amount of metadata fields
        # Must be <= 5 according to Discord docs
        amount_of_metadata_fields = sum(
            1 if issubclass(field_info.annotation, MetadataField) else 0
            for field_info in cls.model_fields.values()
        )
        if amount_of_metadata_fields > 5:
            raise TooManyFieldsException(amount_of_metadata_fields)

        # 2) Not actual check
        # Initialization of values for metadata fields
        for field_name, field_info in cls.model_fields.items():
            if not issubclass(field_info.annotation, MetadataField):
                continue  # do nothing with non-metadata fields

            if field_name not in data:
                continue  # do nothing with empty values

            metadata_field = field_info.annotation(
                **field_info.default.model_dump(exclude_none=True),
                value=data.get(field_name)
            )
            # ugly, need to think about better solution

            data[field_name] = metadata_field

        return data

    @classmethod
    def to_schema(cls) -> list[dict]:
        """Returns a schema of fields as a json string.
        """
        fields = []
        for field_name, field_info in cls.model_fields.items():
            if not issubclass(field_info.annotation, MetadataField):
                # skip non-metadata fields, they should not be present in schema
                continue

            def get_type_of_metadata_field(metadata_model: Type[MetadataField]):
                # Get annotation of field 'value'
                annotation = metadata_model.model_fields['value'].annotation
                # Function get_args(annotation) will produce tuple like
                # (x, NoneType) because `value` field is optional, and it
                # can be represented as Union[x, None]. Just in case it will
                # change somehow, I will not check first element of tuple
                # straight, but check all arguments ...
                for arg in get_args(annotation):
                    # ... and find one which corresponds to my custom class
                    # IntX, DtX or BoolX (they are all listed in FieldType
                    # constraints).
                    if arg in FieldType.__constraints__:
                        # Return class field `type`.
                        return arg.type

            fields.append({
                "type": get_type_of_metadata_field(field_info.annotation),
                **field_info.default.model_dump(exclude_none=True, mode="json")
            })

        return fields

    def to_metadata(self) -> dict[str, Any]:
        platform_data = self.model_dump(exclude_none=True, include={'platform_name', 'platform_username'})

        metadata_fields = {}
        for field_name, field_info in self.model_fields.items():
            if not issubclass(field_info.annotation, MetadataField):
                continue
            field = getattr(self, field_name)
            if field.value is not None:
                metadata_fields[field.key] = field.value

        return {**platform_data, 'metadata': metadata_fields}

    @classmethod
    def from_metadata_response(cls, response: dict) -> Self:
        return cls(
            platform_name=response.get('platform_name'),
            platform_username=response.get('platform_username'),
            **response.get('metadata', {})
        )
