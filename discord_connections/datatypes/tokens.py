from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Self


@dataclass(frozen=True)
class Token:
    access_token: str
    refresh_token: str
    expires_at: datetime

    @classmethod
    def from_token_response(cls, response: dict) -> Self:
        return Token(
            access_token=response['access_token'],
            refresh_token=response['refresh_token'],
            expires_at=datetime.now() + timedelta(seconds=response['expires_in'])
        )
