# ruff: noqa: E402


from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.auth_controller import AuthController
from .controllers.document_file_controller import DocumentFileController
from .controllers.oauth_controller import OAuthController
from .services.document_file_service import DocumentFileService
from .services.partner_service import PartnerService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()
        # Initialize all Services, Controllers, any utils here.
        PartnerService()
        DocumentFileService()

        AuthController().post_init()
        OAuthController().post_init()
        DocumentFileController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)
