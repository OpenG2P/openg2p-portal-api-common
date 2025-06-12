from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, Boolean, Column, Integer, String, Text


class G2PDraftRecordORM(BaseORMModel):
    __tablename__ = "draft_record"

    id = Column(Integer, primary_key=True)  # Assuming an ID column
    name = Column(String)
    given_name = Column(String)
    family_name = Column(String)
    addl_name = Column(String)
    phone = Column(String)
    gender = Column(String)
    region = Column(String)
    is_group = Column(Boolean, default=False)
    partner_data = Column(JSON)  # This will store the full partner_dict as JSON
    state = Column(String, default="draft")
    rejection_reason = Column(Text)
    group_member_ids_json = Column(JSON)
