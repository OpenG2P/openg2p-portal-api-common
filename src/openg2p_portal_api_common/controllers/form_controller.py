from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import (
    UnauthorizedError,
)

from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.form import Form
from ..services.form_service import FormService

_config = Settings.get_config()


class FormController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._form_service = FormService.get_component()

        self.router.prefix = "/common"
        self.router.tags = ["portal common"]

        self.router.add_api_route(
            "/forms",
            self.get_all_form,
            responses={200: {"model": Form}},
            methods=["GET"],
        )

    @property
    def form_service(self):
        if not self._form_service:
            self._form_service = FormService.get_component()
        return self._form_service

    async def get_all_form(
        self,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError(
                message="Unauthorized. Partner Not Found in Registry."
            )
        return await self.form_service.list_all_form()
