from pydantic import PositiveInt

from apps.schedule.domain.schedule import BaseEvent, BasePeriodicity
from apps.shared.domain import PublicModel

__all__ = [
    "PublicPeriodicity",
    "PublicEvent",
    "ActivityEventCount",
    "FlowEventCount",
    "PublicEventCount",
]


class PublicPeriodicity(BasePeriodicity, PublicModel):
    pass


class PublicEvent(BaseEvent, PublicModel):
    id: PositiveInt
    periodicity: PublicPeriodicity
    user_ids: list[int] | None
    activity_id: int | None
    flow_id: int | None


class ActivityEventCount(PublicModel):
    count: int
    activity_id: int
    activity_name: str


class FlowEventCount(PublicModel):
    count: int
    flow_id: int
    flow_name: str


class PublicEventCount(PublicModel):
    activity_events: list[ActivityEventCount] | None
    flow_events: list[FlowEventCount] | None