from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import (
    BadRequestError,
    UnauthorizedError,
)
from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.document_file import DocumentFile
from ..services.document_file_service import DocumentFileService

_config = Settings.get_config()


class DocumentFileController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_service = DocumentFileService.get_component()

        self.router = APIRouter()
        self.router.tags += ["document"]

        self.router.add_api_route(
            "/getDocument/{document_id}",
            self.get_document_by_id,
            responses={200: {"model": DocumentFile}},
            methods=["GET"],
        )

    @property
    def file_service(self):
        if not self._file_service:
            self._file_service = DocumentFileService.get_component()
        return self._file_service

    async def get_document_by_id(
        self,
        document_id: int,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError(
                message="Unauthorized. Partner Not Found in Registry."
            )

        try:
            document = await self.file_service.get_document_by_id(document_id, auth.partner_id)
            return document
        except Exception:
            raise BadRequestError(message="Failed to retrieve document by ID") from None
