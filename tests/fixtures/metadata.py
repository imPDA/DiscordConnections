from collections import ChainMap
from typing import Type, Union, List, Tuple, Any, Optional

import pytest
from pydantic import create_model

from datatypes.base_metadata import MetadataField, BaseMetadata
from datatypes.field_types import *

MetadataFieldType = Union[
    Type[IntLe], Type[IntGe],
    Type[IntEq], Type[IntNe],
    Type[DtLe], Type[DtGe],
    Type[BoolEq], Type[BoolNe]
]


# def create_one_field(type_, name: str, value: Optional[Any] = None) -> dict:
#     annotation = MetadataField[type_]
#     default = MetadataField[type_](**{
#         'key': f'{name}_key',
#         'name': f'{name}_name',
#         'description': f'{name}_description',
#         'value': value
#     })
#
#     return {name: (annotation, default)}


def create_one_field(type_, name: str) -> dict:
    annotation = MetadataField[type_]
    default = MetadataField[type_](**{
        'key': f'{name}_key',
        'name': f'{name}_name',
        'description': f'{name}_description',
    })

    return {name: (annotation, default)}


def create_test_metadata_model(
        *, name: str = None, metadata_fields: List[Tuple[MetadataFieldType, Any]] = None,
        platform_name: str = "Test", platform_username: str = None
) -> Type[BaseMetadata]:
    if not metadata_fields:
        metadata_fields = []

    names = [f"field_{n + 1}" for n in range(len(metadata_fields))]
    types = [f[0] for f in metadata_fields]
    # values = [f[1] for f in model_fields]

    fields = dict(ChainMap(
        *[create_one_field(type_, name) for name, type_ in zip(names, types)]
    ))
    # prettify sorting fields in ascending order by field number
    fields = dict(sorted(fields.items()))

    # add standard fields `platform_name` and `platform_username`
    fields.update({
        'platform_name': (str, platform_name),
        'platform_username': (str, platform_username)
    })

    # if not any(values):
    return create_model(
        name or 'TestMetadataModel', **fields, __base__=BaseMetadata
    )

    # raise NotImplementedError("Values initialization not implemented yet")


@pytest.fixture
def model_name() -> str:
    return NotImplementedError('Model name must be provided via parametrization')  # noqa


@pytest.fixture
def model_fields() -> List[Tuple[MetadataFieldType, Any]]:
    return NotImplementedError('Model fields must be provided via parametrization')  # noqa


@pytest.fixture
def metadata_model(model_name, model_fields) -> Type[BaseMetadata]:
    return create_test_metadata_model(
        name=model_name, metadata_fields=model_fields
    )
