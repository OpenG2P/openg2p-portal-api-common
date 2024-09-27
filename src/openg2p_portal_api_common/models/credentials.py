from openg2p_fastapi_auth.models.credentials import AuthCredentials


class AuthCredentials(AuthCredentials):
    partner_id: int = None
