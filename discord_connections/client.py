import uuid
from typing import TypeVar, Generic, Type
from urllib.parse import urlencode

import httpx

from .datatypes import Token, BaseMetadataModel, Scope
from .exceptions import RequestError

API_URL = "https://discord.com/api/"
OAUTH_URL = API_URL + "/oauth2"
AUTH_URL = OAUTH_URL + "/authorize"
TOKEN_URL = OAUTH_URL + "/token"
ME_URL = OAUTH_URL + "/@me"

ROLE_CONNECTIONS_METADATA_URL = API_URL + "users/@me/applications/{application_id}/role-connection"
ROLE_CONNECTIONS_CONFIGURE_METADATA_URL = API_URL + "applications/{application_id}/role-connections/metadata"

DEFAULT_SCOPES = [Scope.ROLE_CONNECTIONS_WRITE, Scope.IDENTIFY]


MM = TypeVar('MM', bound=BaseMetadataModel)  # MM = Metadata Model


class Client(Generic[MM]):
    def __init__(
        self,
        client_id: int | str,
        client_secret: str,
        redirect_uri: str,
        discord_token: str,
        metadata_model: Type[MM]
    ) -> None:
        self.client_id = int(client_id)
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.discord_token = discord_token
        self._metadata_model = metadata_model

    async def _request(
        self, method: str, url: str, **kwargs
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, **kwargs)

            if response.status_code != 200:
                raise RequestError(response.status_code, response.text)

            return response.json()

    @property
    def oauth_url(self, *additional_scopes: Scope) -> tuple[str, str]:
        """Returns auth link and state (UUID in string, used to verify response).

        NOTE: Scopes `ROLE_CONNECTIONS_WRITE` and `IDENTIFY` are used by default in
        order to let this client control role connections, but additional scopes
        can be passed as arguments.
        """

        scopes = DEFAULT_SCOPES
        scopes.extend(additional_scopes)

        scope_str = ' '.join(map(str, scopes))
        state_str = str(uuid.uuid4())

        query = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state_str,
            'scope': scope_str,
            'prompt': 'consent',
        }

        url = f'{AUTH_URL}?{urlencode(query)}'

        return url, state_str

    async def get_token(self, code: str) -> Token:
        """Returns `Token` object with access and refresh tokens.
        """
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

        response = await self._request(
            'POST', TOKEN_URL, headers=headers, data=data
        )

        return Token.from_token_response(response)

    async def refresh_token(self, token: Token) -> Token:
        """Refreshes `Token`, returns new one.
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token.refresh_token,
        }

        response = await self._request(
            'POST', TOKEN_URL, headers=headers, data=data
        )

        return Token.from_token_response(response)

    async def revoke_token(self, token: Token) -> bool:
        """Revokes `Token`, returns `True` on success.
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'token': token.access_token,
            'token_type_hint': 'access_token'
        }

        await self._request(
            'POST', TOKEN_URL + '/revoke', headers=headers, data=data
        )

        return True

    async def get_user_data(self, token: Token) -> dict:
        """Returns user data from /oauth2/@me endpoint.

        https://discord.com/developers/docs/topics/oauth2#get-current-authorization-information.
        """
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        user_data = await self._request('GET', ME_URL, headers=headers)

        return user_data

    async def push_metadata(self, token: Token, metadata: MM) -> MM:
        """Updates metadata for a particular user with given `Token`.

        Returns the updated metadata on success.
        """
        headers = {
            'Authorization': f'Bearer {token.access_token}',
            'Content-Type': 'application/json',
        }

        response = await self._request(
            'PUT', ROLE_CONNECTIONS_METADATA_URL.format(application_id=self.client_id),
            headers=headers, json=metadata.to_metadata()
        )

        return self._metadata_model.from_metadata_response(response)

    async def get_metadata(self, token: Token) -> MM:
        """Returns current metadata for a particular user with given `Token`.
        """
        headers = {
            'Authorization': f'Bearer {token.access_token}',
        }

        response = await self._request(
            'GET', ROLE_CONNECTIONS_METADATA_URL.format(application_id=self.client_id),
            headers=headers
        )

        return self._metadata_model.from_metadata_response(response)

    async def register_metadata_schema(self, metadata: MM) -> dict:
        """Registers metadata schema for application.

        Returns registered schema on success.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bot {self.discord_token}',
        }

        response = await self._request(
            'PUT', ROLE_CONNECTIONS_CONFIGURE_METADATA_URL.format(application_id=self.client_id),
            headers=headers, json=metadata.to_schema()
        )

        return response
