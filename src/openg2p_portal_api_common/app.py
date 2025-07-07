# ruff: noqa: E402


from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.auth_controller import AuthController
from .controllers.document_file_controller import DocumentFileController
from .controllers.form_controller import FormController
from .controllers.group_controller import GroupController
from .controllers.individual_controller import IndividualController
from .controllers.oauth_controller import OAuthController
from .services.document_file_service import DocumentFileService
from .services.form_service import FormService
from .services.group_service import GroupService
from .services.partner_service import PartnerService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Initialize services
        PartnerService()
        DocumentFileService()
        GroupService()
        FormService()

        # Initialize controllers
        IndividualController().post_init()
        GroupController().post_init()
        DocumentFileController().post_init()
        FormController().post_init()
        AuthController().post_init()
        OAuthController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)
