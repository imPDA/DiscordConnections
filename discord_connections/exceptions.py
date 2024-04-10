from dataclasses import dataclass


@dataclass
class ClientError(Exception):
    @property
    def message(self):
        return "Opps... Unknown error occurred!"


@dataclass
class RequestError(ClientError):
    status_code: int
    msg: str

    @property
    def message(self):
        return f"{self.status_code} returned: {self.msg}"


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
