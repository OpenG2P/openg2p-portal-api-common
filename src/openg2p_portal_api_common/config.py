from typing import Optional

from openg2p_fastapi_auth.config import ApiAuthSettings
from openg2p_fastapi_auth.config import Settings as AuthSettings
from openg2p_fastapi_common.config import Settings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(AuthSettings, Settings):
    model_config = SettingsConfigDict(
        env_prefix="portal_common_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P Portal API Common"
    openapi_description: str = """
    This module implements OpenG2P Portal Common APIs.

    ***********************************
    Further details goes here
    ***********************************
    """

    openapi_version: str = __version__
    db_dbname: Optional[str] = "openg2pdb"

    registrant_draft_mode_enabled: bool = True

    auth_api_update_profile: ApiAuthSettings = ApiAuthSettings(enabled=True)
    auth_api_get_document_by_id: ApiAuthSettings = ApiAuthSettings(enabled=True)
