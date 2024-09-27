import logging
from datetime import datetime

import orjson
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..context import partner_fields_cache
from ..models.orm.auth_oauth_provider import AuthOauthProviderORM
from ..models.orm.partner_orm import PartnerORM, PartnerPhoneNoORM
from ..models.orm.reg_id_orm import RegIDORM

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class PartnerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def check_and_create_partner(
        self, validation: dict, id_type_config: dict = None
    ):
        if not (id_type_config and id_type_config.get("g2p_id_type", None)):
            raise InternalServerError(
                message="Invalid Auth Provider Configuration. ID Type not configured."
            )

        reg_id_res = await RegIDORM.get_partner_by_reg_id(
            id_type_config["g2p_id_type"], validation["sub"]
        )

        if not reg_id_res:
            id_value = validation["sub"]
            validation = AuthOauthProviderORM.map_validation_response(
                validation, id_type_config["token_map"]
            )
            name = validation.pop("name", "")
            partner_dict = {
                "given_name": name.split(" ")[0],
                "family_name": name.split(" ")[-1],
                "addl_name": " ".join(name.split(" ")[1:-1]),
                "email": validation.pop("email", ""),
                "is_registrant": True,
                "is_group": False,
                "active": True,
                "company_id": id_type_config["company_id"],
            }
            partner_dict["name"] = self.create_partner_process_name(
                partner_dict["family_name"],
                partner_dict["given_name"],
                partner_dict["addl_name"],
            )
            partner_dict["gender"] = self.create_partner_process_gender(
                validation.pop("gender", "")
            )
            partner_dict["birthdate"] = self.create_partner_process_birthdate(
                validation.pop("birthdate", None),
                date_format=id_type_config["date_format"],
            )
            phone = validation.pop("phone", "")
            partner_dict["phone"] = phone

            # Image is stored as attachment in odoo. So the following wont work.
            # partner_dict["image_1920"] = self.process_picture(
            #     validation.pop("picture", None)
            # )

            partner_fields = await self.get_partner_fields()
            partner_dict.update(
                self.create_partner_process_other_fields(
                    validation, id_type_config["token_map"], partner_fields
                )
            )

            async_session_maker = async_sessionmaker(
                dbengine.get(), expire_on_commit=False
            )
            async with async_session_maker() as session:
                try:
                    partner = PartnerORM(**partner_dict)
                    reg_id = RegIDORM(
                        partner=partner,
                        id_type=id_type_config["g2p_id_type"],
                        value=id_value,
                    )
                    phone_number = PartnerPhoneNoORM(
                        partner=partner,
                        phone_no=phone,
                    )
                    session.add(partner)
                    session.add(reg_id)
                    session.add(phone_number)

                    await session.commit()
                    await self.create_partner_add_display_name(partner, session)
                except IntegrityError as e:
                    raise InternalServerError(
                        message=f"Could not create partner. {repr(e)}",
                    ) from e

    async def update_partner_info(self, partner_id, data, session=None):
        # Update partner_info with fields from program_registrant_info
        is_create_session = False
        if not session:
            session = async_sessionmaker(dbengine.get())()
            is_create_session = True
        updated_fields = {}
        partner_fields = await self.get_partner_fields()
        for key, value in data.items():
            # if hasattr(partner_info, key) and getattr(partner_info, key) != value:
            # TODO: handle deleted values

            if key in partner_fields and data.get(key, None):
                updated_fields[key] = value
            # TODO: handle the name change
            # name=self.create_partner_process_name(data["family_name"],data["given_name"],data["addl_name"])
        if updated_fields:
            set_clause = ", ".join(
                [f"{key} = '{value}'" for key, value in updated_fields.items()]
            )
            await session.execute(
                text(
                    f"UPDATE {PartnerORM.__tablename__} SET {set_clause} WHERE id='{partner_id}'"
                )
            )
            await session.commit()
        if is_create_session:
            await session.close()
        return updated_fields

    def create_partner_process_gender(self, gender):
        return gender.capitalize()

    def create_partner_process_birthdate(self, birthdate, date_format="%Y/%m/%d"):
        if not birthdate:
            return None
        return datetime.strptime(birthdate, date_format).date()

    def create_partner_process_name(self, family_name, given_name, addl_name):
        name = ""
        if family_name:
            name += family_name + ", "
        if given_name:
            name += given_name + " "
        if addl_name:
            name += addl_name + " "
        return name.upper()

    # def create_partner_process_picture(self, picture):
    #     image_parsed = None
    #     if picture:
    #         with urlopen(picture) as response:
    #             image_parsed = base64.b64encode(response.read())
    #     return image_parsed

    def create_partner_process_other_fields(
        self, validation: dict, mapping: str, partner_fields: list[str]
    ):
        res = {}
        all_fields = [pair.split(":")[0].strip() for pair in mapping.split(" ")]
        for key in list(validation):
            if key in all_fields and key in partner_fields:
                value = validation.pop(key)
                if isinstance(value, dict) or isinstance(value, list):
                    res[key] = orjson.dumps(value).decode()
                else:
                    res[key] = value
        return res

    async def create_partner_add_display_name(self, partner, session):
        try:
            await self.update_partner_info(
                partner.id, {"display_name": partner.name}, session=session
            )
        except IntegrityError:
            _logger.warning("Failed to insert display name. Odoo version maybe 17.0")

    async def get_partner_fields(self):
        partner_field = partner_fields_cache.get()
        if partner_field:
            return partner_field
        partner_field = await PartnerORM.get_partner_fields()
        partner_fields_cache.set(partner_field)
        return partner_field
