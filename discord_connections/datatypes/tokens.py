from datetime import timedelta, datetime
from typing import Optional, Self

from pydantic import BaseModel, model_validator


class DiscordToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: timedelta
    expires_at: Optional[datetime] = None

    @model_validator(mode='after')
    def set_expires_at(self) -> Self:
        if not self.expires_at:
            self.expires_at = datetime.now() + self.expires_in
        return self

    @property
    def expired(self):
        return datetime.now() > self.expires_at


# TODO TZ awareness?
