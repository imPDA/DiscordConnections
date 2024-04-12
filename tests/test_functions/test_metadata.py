import pytest
import pydantic

from datatypes.exceptions import TooManyFieldsException
from datatypes.field_types import *
from tests.utils import error


@pytest.mark.parametrize('model_name, model_fields', [
    ('TestMetaclassModel', [(IntGe, None)] * 5),
    ('TestMetaclassModel', [(DtGe, None)] * 5),
    ('TestMetaclassModel', [(BoolEq, None)] * 5),
])
def test_creation_success(metadata_model):
    metadata_model()


@pytest.mark.parametrize('model_name, model_fields', [
    ('TestMetaclassModel', [(IntGe, None)])
])
@pytest.mark.parametrize('value', [
    1, "1", 1.0, 1/1, "1.0", (lambda: 1)(), 1 + 1, 2.1 - 0.1
])
def test_filling_with_values_success(metadata_model, value):
    metadata_model(field_1=value)


# TODO Dt, Bool


@pytest.mark.parametrize('model_name, model_fields, expected_result, exception', [
    ('TestMetaclassModel', [(IntGe, None)] * 6, *error(TooManyFieldsException, match="6")),
    ('TestMetaclassModel', [(DtGe, None)] * 7, *error(TooManyFieldsException, match="7")),
    ('TestMetaclassModel', [(BoolEq, None)] * 8, *error(TooManyFieldsException, match="8")),
])
def test_creation_fail_too_many_fields(metadata_model, expected_result, exception):
    with exception:
        metadata_model()


@pytest.mark.parametrize('model_name, model_fields', [
    ('TestMetaclassModel', [(IntGe, None)]),
    ('TestMetaclassModel', [(IntLe, None)]),
    ('TestMetaclassModel', [(IntEq, None)]),
    ('TestMetaclassModel', [(IntNe, None)]),
])
@pytest.mark.parametrize('value, expected_result, exception', [
    (0.1, *error(pydantic.ValidationError)),
    ("0.1", *error(pydantic.ValidationError)),
    (.1, *error(pydantic.ValidationError)),
    (".1", *error(pydantic.ValidationError)),
    ("abc", *error(pydantic.ValidationError)),
    ({}, *error(pydantic.ValidationError)),
    ([], *error(pydantic.ValidationError)),
    (lambda x: x, *error(pydantic.ValidationError)),
])
def test_filling_with_values_fail_wrong_type_int(metadata_model, value, expected_result, exception):
    with exception as exc:
        metadata_model(field_1=value)

    validation_error: pydantic.ValidationError = exc.value

    assert len(validation_error.errors()) == 1
    assert validation_error.errors()[0]['loc'] == ("value", )
    assert "Input should be a valid integer" in validation_error.errors()[0]['msg']

# TODO Dt, Bool
