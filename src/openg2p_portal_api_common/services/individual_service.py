import logging
from datetime import datetime
from typing import Dict, Union

import orjson
from fastapi.responses import JSONResponse
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..context import partner_fields_cache
from ..models.individual import GetIndividual, UpdateIndividual
from ..models.orm.draft_record_orm import G2PDraftRecordORM
from ..models.orm.partner_orm import (
    PartnerORM,
    PartnerPhoneNoORM,
)
from ..models.orm.reg_id_orm import RegIDORM, RegIDTypeORM
from ..utils.registrant_utils import get_full_name, parse_full_name

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class IndividualService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parse_full_name = parse_full_name
        self.async_session_maker = async_sessionmaker(
            dbengine.get(), expire_on_commit=False
        )

    async def get_individual(self, individual_id: int) -> GetIndividual:
        if _config.registrant_draft_mode_enabled:
            handler = DraftIndividualHandler(self)
        else:
            handler = DirectIndividualHandler(self)

        async with self.async_session_maker() as session:
            return await handler.get_individual(session, individual_id)

    async def update_individual(
        self, individual_id: int, data: UpdateIndividual
    ) -> Union[GetIndividual, Dict]:
        if _config.registrant_draft_mode_enabled:
            handler = DraftIndividualHandler(self)
        else:
            handler = DirectIndividualHandler(self)

        async with self.async_session_maker() as session:
            return await handler.update_individual(session, individual_id, data)

    async def get_partner_fields(self) -> list[str]:
        cached_fields = partner_fields_cache.get()
        if cached_fields:
            return cached_fields

        partner_fields = await PartnerORM.get_partner_fields()
        partner_fields_cache.set(partner_fields)
        return partner_fields

    async def _get_individual_from_partner_data(
        self, partner_data: PartnerORM
    ) -> GetIndividual:
        partner_ids_data = await RegIDORM.get_all_partner_ids(partner_data.id)
        partner_phone_data = await PartnerPhoneNoORM.get_partner_phone_details(
            partner_data.id
        )

        partner_ids = []
        for reg_id in partner_ids_data:
            partner_id = {
                "id_type": None,
                "value": reg_id.value,
                "expiry_date": reg_id.expiry_date,
            }

            id_type_name = await RegIDTypeORM.get_id_type_name(reg_id.id_type)

            if id_type_name:
                partner_id["id_type"] = id_type_name.name

            partner_ids.append(partner_id)

        partner_phone_numbers = []
        for phone in partner_phone_data:
            partner_phone_numbers.append(
                {
                    "phone_no": phone.phone_no,
                    "date_collected": phone.date_collected,
                }
            )

        return GetIndividual(
            id=partner_data.id,
            reg_ids=partner_ids,
            email=partner_data.email,
            gender=partner_data.gender,
            address=partner_data.address,
            addl_name=partner_data.addl_name,
            given_name=partner_data.given_name,
            family_name=partner_data.family_name,
            birthdate=partner_data.birthdate,
            phone_numbers=partner_phone_numbers,
            birth_place=partner_data.birth_place,
        )


class DraftIndividualHandler:
    def __init__(self, service: IndividualService):
        self.service = service

    async def get_individual(
        self, session: AsyncSession, individual_id: int
    ) -> GetIndividual:
        try:
            draft_record = await session.get(G2PDraftRecordORM, individual_id)
            if not draft_record:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "error_code": 404,
                        "message": f"Draft record not found for individual ID: {individual_id}",
                    },
                )

            # Parse all data from JSON
            partner_data = orjson.loads(draft_record.partner_data)

            # Load reg_ids from Odoo one2many format
            partner_ids = []
            for reg_id_entry in partner_data.get("reg_ids", []):
                reg_id_data = reg_id_entry[2]  # format: [0, "virtual_id", {dict}]
                i = reg_id_data.get("id_type")
                name_obj = await RegIDTypeORM.get_id_type_name(i)

                partner_ids.append(
                    {
                        "id_type": name_obj.name,
                        "status": reg_id_data.get("status"),
                        "value": reg_id_data.get("value"),
                        "expiry_date": reg_id_data.get("expiry_date"),
                    }
                )

            # Load phone_numbers from Odoo one2many format
            partner_phone_numbers = []
            for phone_entry in partner_data.get("phone_number_ids", []):
                phone_data = phone_entry[2]
                partner_phone_numbers.append(
                    {
                        "phone_no": phone_data.get("phone_no"),
                        "date_collected": phone_data.get("date_collected"),
                    }
                )

            return GetIndividual(
                id=individual_id,
                reg_ids=partner_ids,
                email=partner_data.get("email"),
                gender=partner_data.get("gender"),
                address=partner_data.get("address"),
                addl_name=partner_data.get("addl_name"),
                given_name=partner_data.get("given_name"),
                family_name=partner_data.get("family_name"),
                birthdate=partner_data.get("birthdate"),
                phone_numbers=partner_phone_numbers,
                birth_place=partner_data.get("birth_place"),
            )

        except Exception as e:
            _logger.exception(f"Failed to get draft individual {individual_id}")
            raise InternalServerError(
                message=f"Could not retrieve draft individual--{e}"
            ) from e

    async def update_individual(
        self, session: AsyncSession, individual_id: int, data: UpdateIndividual
    ) -> GetIndividual:
        try:
            draft_record = await session.get(G2PDraftRecordORM, individual_id)

            if not draft_record:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "error_code": 404,
                        "message": f"Draft record not found for individual ID: {individual_id}",
                    },
                )

            # Load existing partner_data JSON
            partner_data = orjson.loads(draft_record.partner_data)
            updated_fields = {}

            all_fields = draft_record.get_all_draft_orm_fields()

            for field in all_fields:
                value = getattr(data, field, None)
                print(field, value)
                if value is not None:
                    partner_data[field] = value
                    updated_fields[field] = value

            # Handle reg_ids
            if data.reg_ids:
                formatted_reg_ids = []
                for idx, new_reg in enumerate(data.reg_ids):
                    reg_type = await RegIDTypeORM.get_id_type_by_name(new_reg.id_type)
                    if not reg_type:
                        raise ValueError(f"Invalid ID type: {new_reg.id_type}")
                    reg_type_id = reg_type.id

                    reg_entry = {
                        "id_type": reg_type_id,
                        "value": new_reg.value,
                        "expiry_date": new_reg.expiry_date or False,
                        "status": "",
                        "description": False,
                    }
                    formatted_reg_ids.append([0, f"virtual_reg_id_{idx}", reg_entry])

                partner_data["reg_ids"] = formatted_reg_ids
                updated_fields["reg_ids"] = formatted_reg_ids

            # Handle phone_numbers
            if data.phone_numbers:
                formatted_phones = []
                for idx, phone in enumerate(data.phone_numbers):
                    phone_entry = {
                        "phone_no": phone.phone_no,
                        "country_id": False,
                        "date_collected": datetime.now().strftime("%Y-%m-%d"),
                        "disabled": False,
                    }
                    formatted_phones.append([0, f"virtual_phone_id_{idx}", phone_entry])

                partner_data["phone_number_ids"] = formatted_phones
                updated_fields["phone_number_ids"] = formatted_phones

            if updated_fields:
                draft_record.partner_data = orjson.dumps(partner_data).decode("utf-8")
                await session.commit()
                _logger.info(f"Successfully updated draft individual {individual_id}")
            else:
                _logger.info(f"No changes made to draft individual {individual_id}")

            return await self.get_individual(session, individual_id)

        except Exception as e:
            _logger.exception(f"Failed to update draft individual {individual_id}")
            await session.rollback()
            raise InternalServerError(
                message=f"Could not update draft individual: {e}"
            ) from e


class DirectIndividualHandler:
    def __init__(self, service: IndividualService):
        self.service = service

    async def get_individual(
        self, session: AsyncSession, individual_id: int
    ) -> GetIndividual:
        try:
            partner_data = await PartnerORM.get_partner_data(individual_id)
            return await self.service._get_individual_from_partner_data(partner_data)
        except Exception as e:
            _logger.exception(f"Failed to get individual {individual_id}")
            raise InternalServerError(message="Could not retrieve individual") from e

    async def update_individual(
        self, session: AsyncSession, individual_id: int, data: UpdateIndividual
    ) -> GetIndividual:
        try:
            partner_fields = await self.service.get_partner_fields()
            data_dict = data.model_dump(exclude_unset=True)

            partner_obj = await session.get(PartnerORM, individual_id)
            if not partner_obj:
                raise InternalServerError(
                    message=f"Partner with ID {individual_id} not found"
                )

            for key, value in data_dict.items():
                if key in partner_fields and value is not None:
                    setattr(partner_obj, key, value)

            partner_obj.name = get_full_name(
                data_dict.get("given_name", ""),
                data_dict.get("addl_name", ""),
                data_dict.get("family_name", ""),
            )
            # Update or insert reg_ids
            if data.reg_ids:
                existing_reg_ids_result = await session.execute(
                    select(RegIDORM).where(RegIDORM.partner_id == individual_id)
                )
                existing_reg_ids = {
                    reg.id_type: reg for reg in existing_reg_ids_result.scalars().all()
                }
                for new_reg in data.reg_ids:
                    # Convert name (e.g., 'National id') to id (e.g., 1)
                    reg_type = await RegIDTypeORM.get_id_type_by_name(new_reg.id_type)
                    if not reg_type:
                        raise ValueError(f"Invalid ID type: {new_reg.id_type}")
                    reg_type_id = reg_type.id

                    if reg_type_id in existing_reg_ids:
                        reg_obj = existing_reg_ids[reg_type_id]
                        reg_obj.value = new_reg.value
                        reg_obj.status = new_reg.status
                        reg_obj.expiry_date = new_reg.expiry_date
                    else:
                        session.add(
                            RegIDORM(
                                partner_id=individual_id,
                                id_type=reg_type_id,
                                value=new_reg.value,
                                status=new_reg.status,
                                expiry_date=new_reg.expiry_date,
                            )
                        )

            # Remove all existing phone numbers and insert new ones
            if data.phone_numbers is not None:
                await session.execute(
                    delete(PartnerPhoneNoORM).where(
                        PartnerPhoneNoORM.partner_id == individual_id
                    )
                )
                for phone in data.phone_numbers:
                    session.add(
                        PartnerPhoneNoORM(
                            partner_id=individual_id,
                            phone_no=phone.phone_no,
                            date_collected=phone.date_collected,
                        )
                    )

            await session.commit()
            _logger.info(f"Successfully updated individual {individual_id}")

            return await self.get_individual(session, individual_id)

        except Exception as e:
            _logger.exception(f"Failed to update individual {individual_id}")
            await session.rollback()
            raise InternalServerError(
                message=f"Could not update individual: {e}"
            ) from e
