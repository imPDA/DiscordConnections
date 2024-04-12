from dataclasses import dataclass


@dataclass(eq=False)
class MetadataBaseException(Exception):
    @property
    def message(self):
        return "Unspecified metadata exception"


@dataclass(eq=False)
class TooManyFieldsException(MetadataBaseException):
    num: int

    @property
    def message(self):
        return f"Too many metadata fields ({self.num} received, max 5)"
