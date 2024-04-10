"""
https://discord.com/developers/docs/resources/application-role-connection-metadata#application-role-connection-metadata-object-application-role-connection-metadata-type
"""
from datetime import datetime
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema


__all__ = (
    "IntLe", "IntGe", "IntEq", "IntNe", "DtLe", "DtGe", "BoolEq", "BoolNe"
)


class Int:
    @classmethod
    def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return handler.generate_schema(int)
        # return core_schema.int_schema()  # do I have to pass smth here?


class Dt:
    @classmethod
    def __get_pydantic_core_schema__(
            cls, source: type, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return handler.generate_schema(datetime)
        # return core_schema.datetime_schema()  # do I have to pass smth here?


class Bool:
    @classmethod
    def __get_pydantic_core_schema__(
            cls, source: type, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return handler.generate_schema(bool)
        # return core_schema.bool_schema()  # do I have to pass smth here?


class IntLe(Int):
    type = 1


class IntGe(Int):
    type = 2


class IntEq(Int):
    type = 3


class IntNe(Int):
    type = 4


class DtLe(Dt):
    type = 5


class DtGe(Dt):
    type = 6


class BoolEq(Bool):
    type = 7


class BoolNe(Bool):
    type = 8
