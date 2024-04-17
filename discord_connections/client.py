import uuid
from urllib.parse import urlencode

import httpx

from .datatypes import DiscordToken, BaseMetadata, Scope
from .exceptions import RequestError


API_URL = "https://discord.com/api/"
OAUTH_URL = API_URL + "/oauth2"
AUTH_URL = OAUTH_URL + "/authorize"
TOKEN_URL = OAUTH_URL + "/token"
ME_URL = OAUTH_URL + "/@me"

ROLE_CONNECTIONS_METADATA_URL = API_URL + "users/@me/applications/{application_id}/role-connection"
ROLE_CONNECTIONS_CONFIGURE_METADATA_URL = API_URL + "applications/{application_id}/role-connections/metadata"


class DiscordConnections:
    def __init__(
            self, client_id: int | str, redirect_uri: str, client_secret: str, discord_token: str
    ) -> None:
        self.client_id = int(client_id)
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.discord_token = discord_token

    # TODO headers and data to kwargs
    async def _request(
            self, method: str, url: str, *, headers: dict, **kwargs
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)

            if response.status_code != 200:
                raise RequestError(response.status_code, response.text)

            return response.json()

    @property
    def oauth_url(self, *, add_scopes: list[Scope] = None) -> tuple[str, str]:
        """
        Returns auth link and UUID (in string) to check if response is correct
        """

        scope = ' '.join(map(str, [Scope.ROLE_CONNECTIONS_WRITE, Scope.IDENTIFY, *(add_scopes or [])]))

        state = str(uuid.uuid4())
        query = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': scope,
            'prompt': 'consent',
        }

        # url = f'https://discord.com/api/oauth2/authorize?{urlencode(query)}'
        url = f'{AUTH_URL}?{urlencode(query)}'

        return url, state

    async def get_oauth_token(self, code: str) -> DiscordToken:
        # URL = 'https://discord.com/api/v10/oauth2/token'
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

        token_data = await self._request('POST', TOKEN_URL, headers=headers, data=data)
        return DiscordToken(**token_data)

    async def refresh_token(self, token: DiscordToken) -> DiscordToken:
        # URL = 'https://discord.com/api/v10/oauth2/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token.refresh_token,
        }

        token_data = await self._request('POST', TOKEN_URL, headers=headers, data=data)
        return DiscordToken(**token_data)

    async def get_user_data(self, token: DiscordToken) -> dict:
        # URL = 'https://discord.com/api/v10/oauth2/@me'
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        user_data = await self._request('GET', ME_URL, headers=headers)
        return user_data

    async def push_metadata(self, token: DiscordToken, metadata: BaseMetadata) -> None:
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json',
        }

        metadata = {
            **metadata.model_dump(exclude_none=True, include={'platform_name', 'platform_username'}),
            'metadata': metadata.model_dump(exclude_none=True, exclude={'platform_name', 'platform_username'})
        }

        await self._request(
            'PUT', ROLE_CONNECTIONS_METADATA_URL.format(application_id=self.client_id),
            headers=headers, json=metadata
        )

    async def get_metadata(self, token: DiscordToken) -> dict:
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        return await self._request(
            'GET', ROLE_CONNECTIONS_METADATA_URL.format(application_id=self.client_id),
            headers=headers
        )

    async def register_metadata_schema(self, metadata: BaseMetadata) -> dict:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bot {self.discord_token}',
        }

        return await self._request(
            'PUT', ROLE_CONNECTIONS_CONFIGURE_METADATA_URL.format(application_id=self.client_id),
            headers=headers, json=metadata.to_schema()
        )


Client = DiscordConnections
