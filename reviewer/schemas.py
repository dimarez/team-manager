import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from reviewer.teams.schemas import GitUser


class MrSetupAnswer(BaseModel):
    mr_id: int
    mr_assignee: Optional[GitUser]
    mr_author: GitUser
    mr_reviewers: list[GitUser]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_id: int
    project_name: str
    review_channel: Optional[str]
    review_team: str
    review_lead: Optional[GitUser]
    mr_url: HttpUrl
    timestamp: datetime.datetime = datetime.datetime.now()
