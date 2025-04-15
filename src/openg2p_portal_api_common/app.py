# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.auth_controller import AuthController
from .controllers.oauth_controller import OAuthController
from .controllers.form_controller import FormController
from .services.partner_service import PartnerService
from .services.form_service import FormService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()
        
        PartnerService()
        FormService()
        
        
        FormController().post_init()
        AuthController().post_init()
        OAuthController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

