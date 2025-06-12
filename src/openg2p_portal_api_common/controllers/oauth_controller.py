import orjson
from fastapi import Request
from openg2p_fastapi_auth.controllers.oauth_controller import OAuthController
from openg2p_fastapi_common.utils import cookie_utils

from ..config import Settings
from ..models.orm.auth_oauth_provider import AuthOauthProviderORM
from ..services.partner_service import PartnerService

_config = Settings.get_config()


class OAuthController(OAuthController):
    """
    OAuthController handles OAuth authentication flows and callbacks.
    """

    def __init__(self, **kwargs):
        """
        Initializes the OAuthController with necessary components and configurations.
        """
        super().__init__(**kwargs)
        self.partner_service = PartnerService.get_component()

    async def oauth_callback(self, request: Request):
        """
        Handles the OAuth callback after a user has authenticated with an OAuth provider.

        Args:

            request (Request): The incoming request object containing the OAuth data.

        Returns:

            The response object after processing the OAuth callback.
        """
        query_params = request.query_params
        state = orjson.loads(query_params.get("state", "{}"))
        auth_provider_id = state.get("p", None)

        res = await super().oauth_callback(request)

        userinfo_dict = await self.auth_controller.get_oauth_validation_data(
            auth=cookie_utils.get_response_cookies(res, "X-Access-Token")[-1],
            id_token=cookie_utils.get_response_cookies(res, "X-ID-Token")[-1],
            provider=await self.auth_controller.get_login_provider_db_by_id(
                auth_provider_id
            ),
        )

        id_type_config = await AuthOauthProviderORM.get_auth_id_type_config(
            id=auth_provider_id
        )
        await self.partner_service.check_and_create_partner(
            userinfo_dict, id_type_config=id_type_config
        )

        return res
