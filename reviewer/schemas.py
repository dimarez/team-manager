import datetime

from pydantic import BaseModel

from reviewer.teams.schemas import User


class MrSetupAnswer(BaseModel):
    mr_id: int
    author: User
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_id: int
    project_name: str
    web_url: str
    reviewer: User
    timestamp: datetime.datetime = datetime.datetime.now()
