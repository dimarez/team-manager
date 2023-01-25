import datetime

from pydantic import BaseModel, HttpUrl

from reviewer.teams.schemas import User


class MrSetupAnswer(BaseModel):
    mr_id: int
    mr_author: User
    mr_reviewer: User
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_id: int
    project_name: str
    web_url: HttpUrl
    timestamp: datetime.datetime = datetime.datetime.now()
