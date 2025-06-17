# ruff: noqa: E402


from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.auth_controller import AuthController
from .controllers.document_file_controller import DocumentFileController
from .controllers.form_controller import FormController
from .controllers.group_controller import GroupController
from .controllers.oauth_controller import OAuthController
from .services.document_file_service import DocumentFileService
from .services.form_service import FormService
from .services.group_service import GroupService
from .services.partner_service import PartnerService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()
        # Initialize all Services, Controllers, any utils here.
        PartnerService()
        DocumentFileService()
        GroupService()
        FormService()

        AuthController().post_init()
        OAuthController().post_init()
        DocumentFileController().post_init()
        GroupController().post_init()
        FormController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)
