from dataclasses import dataclass


@dataclass
class ClientError(Exception):
    @property
    def message(self):
        return "Client error occurred."


@dataclass
class RequestError(ClientError):
    status_code: int
    response_message: str

    @property
    def message(self):
        return f"Error occurred during request.\nStatus code: {self.status_code}\nResponse: {self.response_message}"


# class GetOAuthTokenError(RequestError):
#     @property
#     def message(self):
#         return f"Error with token request: {super().message}"
#
#
# class RefreshTokenError(RequestError):
#     @property
#     def message(self):
#         return f"Error with token refresh: {super().message}"
#
#
# class GetUserDataError(RequestError):
#     @property
#     def message(self):
#         return f"Error retrieving user data: {super().message}"
