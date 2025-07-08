from typing import Annotated, Union

from fastapi import Depends
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from sqlalchemy.exc import IntegrityError

from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.individual import GetIndividual, UpdateIndividual
from ..services.individual_service import IndividualService

_config = Settings.get_config()


class IndividualController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._individual_service = IndividualService.get_component()

        self.router.tags += ["individual"]

        self.router.add_api_route(
            "/individual",
            self.get_individual,
            responses={200: {"model": GetIndividual}},
            methods=["GET"],
        )
        self.router.add_api_route(
            "/individual",
            self.update_individual,
            methods=["PUT"],
        )

    @property
    def individual_service(self):
        if not self._individual_service:
            return IndividualService.get_component()
        return self._individual_service

    async def get_individual(
        self, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
    ) -> GetIndividual:
        if not auth.partner_id:
            raise UnauthorizedError(
                message="Unauthorized. Partner Not Found in Registry."
            )

        return await self.individual_service.get_individual(auth.partner_id)

    async def update_individual(
        self,
        userdata: UpdateIndividual,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> Union[GetIndividual, dict]:
        try:
            return await self.individual_service.update_individual(
                auth.partner_id, userdata
            )
        except IntegrityError:
            return {
                "status": "error",
                "status_code": 400,
                "message": "Could not update individual due to integrity constraint.",
            }
