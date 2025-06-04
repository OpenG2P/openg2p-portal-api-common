# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.auth_controller import AuthController
from .controllers.oauth_controller import OAuthController
from .controllers.form_controller import FormController
from .controllers.group_controller import GroupController
from .controllers.document_file_controller import DocumentFileController

from .services.partner_service import PartnerService
from .services.form_service import FormService
from .services.group_services import GroupService
from .services.document_file_service import DocumentFileService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()

        PartnerService()
        FormService()
        GroupService()
        DocumentFileService()

        AuthController().post_init()
        OAuthController().post_init()

        FormController().post_init()
        GroupController().post_init()
        DocumentFileController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)
