from typing import Optional

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from openg2p_fastapi_auth.dependencies import JwtBearerAuth
from openg2p_fastapi_auth.models.credentials import (
    AuthCredentials as OriginalAuthCredentials,
)
from openg2p_fastapi_common.errors.http_exceptions import (
    InternalServerError,
    UnauthorizedError,
)

from .models.credentials import AuthCredentials
from .models.orm.auth_oauth_provider import AuthOauthProviderORM
from .models.orm.reg_id_orm import RegIDORM


class JwtBearerAuth(JwtBearerAuth):
    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        res: OriginalAuthCredentials = await super().__call__(request)
        if not res:
            return None

        id_type_config = await AuthOauthProviderORM.get_auth_id_type_config(iss=res.iss)
        if not (id_type_config and id_type_config.get("g2p_id_type", None)):
            raise InternalServerError(
                message="Unauthorized. Invalid Auth Provider. ID Type not configured."
            )

        partners = await RegIDORM.get_partner_by_reg_id(
            id_type_config["g2p_id_type"], res.sub
        )
        if not partners:
            raise UnauthorizedError(
                message="Unauthorized. Partner Not Found in Registry."
            )
        partner = partners[0]

        new_res = AuthCredentials(partner_id=partner.partner_id, **res.model_dump())

        return new_res
