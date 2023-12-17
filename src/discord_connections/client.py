import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
import json

from .datatypes import DiscordToken, Metadata, MetadataField, Scope
from .exceptions import RequestError


class DiscordConnections:
    def __init__(self, client_id: int | str, redirect_uri: str, client_secret: str, discord_token: str):
        self.client_id = int(client_id)
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.discord_token = discord_token

    async def _request(self, method: str, url: str, headers: dict, data: dict = None) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, data=data, headers=headers)

            if response.status_code != 200:
                raise RequestError(response.status_code, response.text)

            return response.json()

    @property
    def oauth_url(self, *, add_scopes: list[Scope] = None) -> tuple[str, str]:
        """
        Returns auth link and UUID (in string) to check if response is correct
        """

        scope = ' '.join(map(str, [Scope.ROLE_CONNECTION_WRITE, Scope.IDENTIFY, *(add_scopes or [])]))

        state = str(uuid.uuid4())
        query = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': scope,
            'prompt': 'consent',
        }

        url = f'https://discord.com/api/oauth2/authorize?{urlencode(query)}'

        return url, state

    async def get_oauth_token(self, code: str) -> DiscordToken:
        URL = 'https://discord.com/api/v10/oauth2/token'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
        }

        token_data = await self._request('POST', URL, headers, data)
        return DiscordToken(**token_data)

    async def refresh_token(self, token: DiscordToken) -> DiscordToken:
        URL = 'https://discord.com/api/v10/oauth2/token'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token.refresh_token,
        }

        token_data = await self._request('POST', URL, headers, data)
        return DiscordToken(**token_data)

    async def get_user_data(self, token: DiscordToken) -> dict:
        URL = 'https://discord.com/api/v10/oauth2/@me'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        user_data = await self._request('GET', URL, headers)
        return user_data

    async def push_metadata(self, token: DiscordToken, metadata: Metadata) -> None:
        URL = f'https://discord.com/api/v10/users/@me/applications/{self.client_id}/role-connection'

        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json',
        }

        await self._request('PUT', URL, headers, data=json.dumps(metadata.to_dict()))  # noqa

    async def get_metadata(self, token: DiscordToken) -> dict:
        URL = f'https://discord.com/api/v10/users/@me/applications/{self.client_id}/role-connection'

        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        return await self._request('GET', URL, headers)

    async def register_metadata_schema(self, metadata: Metadata) -> dict:
        URL = f'https://discord.com/api/v10/applications/{self.client_id}/role-connections/metadata'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bot {self.discord_token}',
        }

        return await self._request('PUT', URL, headers, data=json.dumps(metadata.to_schema()))  # noqa


Client = DiscordConnections
