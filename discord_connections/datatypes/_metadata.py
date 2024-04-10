"""
https://discord.com/developers/docs/resources/application-role-connection-metadata
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum


class MetadataType(Enum):
    INT_LTE = 1
    INT_GTE = 2
    INT_EQ = 3
    INT_NE = 4
    DT_LTE = 5
    DT_GTE = 6
    BOOL_EQ = 7
    BOOL_NE = 8

    def __repr__(self):
        return str(self.value)


KEY_PATTERN = re.compile(r'[a-z0-9_]*')


class MetadataField:
    def __init__(
            self,
            field_type: MetadataType,
            name: str,
            description: str,
            *,
            key: str = None,
            name_localizations: dict = None,
            description_localization: dict = None
    ):
        self._type = field_type
        self._value = None
        self._key = key
        self._name = name
        self._name_localizations = name_localizations
        self._description = description
        self._description_localization = description_localization

        self._validate()

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if not KEY_PATTERN.fullmatch(value):
            raise ValueError("Only a-z, 0-9, or _ characters can be used")
        self._key = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._is_valid_value(value):
            self._value = value

    def __repr__(self):
        return f"{self.__class__.__name__} <{self._name}: {self._value} {self._description}>"

    def __call__(self, *args, **kwargs):
        return MetadataField(
            field_type=self._type,
            key=self._key,
            name=self._name,
            description=self._description,
            name_localizations=self._name_localizations,
            description_localization=self._description_localization
        )

    def to_dict(self):
        return {
            'type': self._type.value,
            'key': self._key,
            'name': self._name,
            'description': self._description,
            'name_localizations': self._name_localizations,
            'description_localizations': self._description_localization
        }

    def _validate(self):
        self._validate_name()
        self._validate_description()

    def _is_valid_value(self, value):
        if value is None:
            return True
        match self._type:
            case MetadataType.INT_LTE | MetadataType.INT_GTE | MetadataType.INT_EQ | MetadataType.INT_NE:
                if not isinstance(value, int):
                    raise ValueError('Value must me an integer')
            case MetadataType.DT_LTE | MetadataType.DT_GTE:
                if not isinstance(value, datetime):
                    raise ValueError('Value must me a datetime')
            case MetadataType.BOOL_EQ | MetadataType.BOOL_NE:
                if not isinstance(value, bool):
                    raise ValueError('Value must me a boolean')
        return True

    def _validate_key(self):
        if not isinstance(self._key, str):
            raise ValueError('Key must me a string')
        if not 1 <= len(self._key) <= 50:
            raise ValueError('Key must be from 1 to 50 characters long')
        return True

    def _validate_name(self):
        if not isinstance(self._name, str):
            raise ValueError('Name must me a string')
        if not 1 <= len(self._name) <= 100:
            raise ValueError('Name must be from 1 to 100 characters long')
        return True

    def _validate_description(self):
        if not isinstance(self._description, str):
            raise ValueError('Description must me a string')
        if not 1 <= len(self._description) <= 200:
            raise ValueError('Description must be from 1 to 200 characters long')
        return True


class MetadataBase(type):
    platform_name: str = None
    platform_username: str = None

    def __new__(cls, clsname, superclasses, attributedict):
        parents = [s for s in superclasses if isinstance(s, MetadataBase)]

        if not parents:
            return super().__new__(cls, clsname, superclasses, attributedict)

        custom_fields = {k: v for k, v in attributedict.items() if not k.startswith('__') and k not in cls.__dict__}

        if not all([isinstance(v, MetadataField) for v in custom_fields.values()]):
            raise ValueError('All custom fields must be `MetadataFieldMeta` instances only')

        if not 1 <= len(custom_fields) <= 5:
            raise ValueError(f'From 1 to 5 custom fields available only ({len(custom_fields)} provided)')

        for field_name, field_value in custom_fields.items():
            field_value.key = field_name

        attributedict.update(custom_fields)

        return super().__new__(cls, clsname, superclasses, attributedict)

    def __init__(cls, clsname, superclasses, attributedict):
        parents = [s for s in superclasses if isinstance(s, MetadataBase)]

        if parents:
            if not cls.platform_name:
                raise ValueError('`platform_name` must be set up')

            if not isinstance(cls.platform_name, str):
                ValueError('`platform_name` must be a `str`')

            # if 'platform_username' not in attributedict:
            #     attributedict.update({'platform_username': None})
            #
            # print(attributedict)

        super().__init__(clsname, superclasses, attributedict)


class Metadata(metaclass=MetadataBase):
    def __init__(self, args: dict = None, /, **kwargs):
        self.platform_name: str | None
        self.platform_username: str | None

        custom_fields = [k for k in dir(self) if isinstance(getattr(self, k), MetadataField)]
        for f in custom_fields:
            self.__dict__[f] = getattr(self, f)()

        if 'platform_username' not in dir(self):
            self.platform_username = None
        custom_fields.append('platform_username')

        if args and kwargs:
            raise ValueError('Only args OR kwargs can be provided at the same time')

        if args:
            kwargs = args

        for k, v in kwargs.items():
            if k not in custom_fields:
                raise ValueError(f'Unknown field `{k}`')

            setattr(self, k, v)

    def __setattr__(self, key, value):
        try:
            item_value = self.__dict__[key]  # ???
        except KeyError:
            super().__setattr__(key, value)
            return

        if isinstance(item_value, MetadataField):
            item_value.value = value
        else:
            super().__setattr__(key, value)

    def to_dict(self):
        output = {
            'platform_name': self.platform_name,
            'platform_username': self.platform_username,
            'metadata': {
                v.key: v.value for v in self.__dict__.values() if isinstance(v, MetadataField) and v.value is not None
            }  # null is not permitted in discord metadata, so we check if v.value is not none
        }

        return {k: v for k, v in output.items() if v is not None}  # null is not permitted in discord metadata

    @classmethod
    def to_schema(cls):
        output = [v.to_dict() for v in cls.__dict__.values() if isinstance(v, MetadataField)]
        return output

    def __repr__(self):
        return f"{self.__class__.__name__}({self.to_dict()})"

    # def __getattribute__(self, item):
    #     item_value = super().__getattribute__(item)
    #     if isinstance(item_value, MetadataField):
    #         return item_value.value
    #     else:
    #         return item_value


# TODO refactor EVERYTHING HERE
