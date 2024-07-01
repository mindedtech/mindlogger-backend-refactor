import datetime
import uuid
from enum import Enum

from pydantic import BaseModel, Extra

from apps.activities.domain.conditional_logic import ConditionalLogic

__all__ = [
    "UnencryptedAppletVersion",
    "UnencryptedApplet",
    "Consent",
    "ConsentUpdate",
    "ConsentCreate",
    "PublicConsent",
    "ConsentRequest",
    "ConsentUpdateRequest",
    "PublicListOfVisits",
    "PublicListMultipleVisits",
]


class Item(BaseModel):
    id: uuid.UUID
    question: str
    responseType: str
    responseValues: dict | None
    config: dict | None
    name: str
    isHidden: bool | None
    conditionalLogic: ConditionalLogic | None
    allowEdit: bool | None


class Activitie(BaseModel):
    id: str
    name: str
    description: str
    splash_screen: str = ""
    image: str = ""
    order: int
    createdAt: datetime.datetime
    items: list[Item]


class UnencryptedApplet(BaseModel):
    id: uuid.UUID
    displayName: str
    description: str
    activities: list[Activitie]


class UnencryptedAppletVersion(BaseModel):
    version: str
    applet: UnencryptedApplet


class LorisServerResponse(BaseModel):
    pass


def to_camelcase(payload: str) -> str:
    if "_" not in payload:
        return payload

    return "".join(word.capitalize() if index else word for index, word in enumerate(payload.split("_")))


class InternalModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True
        validate_assignment = True
        alias_generator = to_camelcase


class ConsentCreate(InternalModel):
    user_id: uuid.UUID
    is_ready_share_data: bool
    is_ready_share_media_data: bool


class ConsentUpdate(ConsentCreate):
    pass


class Consent(ConsentCreate, InternalModel):
    id: uuid.UUID


class PublicConsent(ConsentCreate):
    pass


class ConsentRequest(ConsentCreate):
    pass


class ConsentUpdateRequest(ConsentUpdate):
    pass


class MlLorisUserRelationshipBase(InternalModel):
    ml_user_uuid: uuid.UUID
    loris_user_id: str


class MlLorisUserRelationshipCreate(MlLorisUserRelationshipBase):
    pass


class MlLorisUserRelationship(MlLorisUserRelationshipBase):
    pass


class PublicListOfVisits(InternalModel):
    visits: list[str]
    count: int


class ActivitiesAndVisitsInternal(InternalModel):
    activity_id: str
    activity_name: str
    answer_id: str
    version: str
    completed_date: datetime.datetime
    visits: list[str]


class UsersAndVisits(InternalModel):
    user_id: str
    secret_user_id: str
    activities: list[ActivitiesAndVisitsInternal]


class PublicListMultipleVisits(InternalModel):
    info: list[UsersAndVisits]
    count: int


class ActivitiesAndVisits(InternalModel):
    activity_id: uuid.UUID
    answer_id: uuid.UUID
    version: str
    visit: str


class VisitsForUsers(InternalModel):
    user_id: uuid.UUID
    activities: list[ActivitiesAndVisits]


class LorisIntegrationAlertMessages(str, Enum):
    LORIS_INTEGRATION = "Loris Integration: "
    NO_RESPONDENT = LORIS_INTEGRATION + "No respondent found."
    REPORT_SERVER = LORIS_INTEGRATION + "Error during request to report server."
    SUCCESS = LORIS_INTEGRATION + "Successful synchronization."
    LORIS_SERVER_ERROR = LORIS_INTEGRATION + "Loris server error."
    LORIS_LOGIN_ERROR = LORIS_INTEGRATION + "Incorrect credentials for Loris server."
