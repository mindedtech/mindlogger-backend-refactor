import uuid
from datetime import datetime

from pydantic import Field

from apps.activities.domain.activity_base import ActivityBase
from apps.activities.domain.activity_item import (
    ActivityItemDuplicate,
    ActivityItemSingleLanguageDetail,
    ActivityItemSingleLanguageDetailPublic,
)
from apps.activities.domain.scores_reports import ScoresAndReportsMobile
from apps.shared.domain import InternalModel, PublicModel


class Activity(ActivityBase, InternalModel):
    id: uuid.UUID
    order: int


class ActivityDuplicate(ActivityBase, InternalModel):
    id: uuid.UUID
    key: uuid.UUID
    order: int
    items: list[ActivityItemDuplicate] = Field(default_factory=list)


class ActivityPublic(ActivityBase, InternalModel):
    id: uuid.UUID
    order: int


class ActivitySingleLanguageDetail(ActivityBase, InternalModel):
    id: uuid.UUID
    order: int
    description: str  # type: ignore[assignment]
    created_at: datetime


class ActivitySingleLanguageDetailPublic(ActivityBase, PublicModel):
    id: uuid.UUID
    order: int
    description: str  # type: ignore[assignment]
    created_at: datetime


class ActivitySingleLanguageMobileDetailPublic(InternalModel):
    id: uuid.UUID
    name: str
    description: str
    image: str = ""
    is_reviewable: bool = False
    is_skippable: bool = False
    show_all_at_once: bool = False
    is_hidden: bool | None = False
    response_is_editable: bool = False
    order: int
    splash_screen: str = ""


class ActivitySingleLanguageWithItemsDetail(ActivityBase, InternalModel):
    id: uuid.UUID
    order: int
    description: str  # type: ignore[assignment]
    items: list[ActivityItemSingleLanguageDetail] = Field(default_factory=list)
    created_at: datetime


class ActivitySingleLanguageWithItemsDetailPublic(ActivityBase, PublicModel):
    id: uuid.UUID
    order: int
    description: str  # type: ignore[assignment]
    items: list[ActivityItemSingleLanguageDetailPublic] = Field(
        default_factory=list
    )
    created_at: datetime


class ActivityLanguageWithItemsMobileDetailPublic(PublicModel):
    id: uuid.UUID
    name: str
    description: str
    splash_screen: str = ""
    image: str = ""
    show_all_at_once: bool = False
    is_skippable: bool = False
    is_reviewable: bool = False
    is_hidden: bool | None = False
    response_is_editable: bool = False
    order: int
    items: list[ActivityItemSingleLanguageDetailPublic] = Field(
        default_factory=list
    )
    scores_and_reports: ScoresAndReportsMobile | None = None
