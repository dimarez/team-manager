from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    team: str
    lead: str
    id: int
    name: Optional[str]
    email: str
    avatar_url: Optional[str]
    web_url: Optional[str]


class Config(BaseModel):
    GITLAB_TOKEN: str
    CI_SERVER_URL: str
    MERGE_REQUEST_IID: int
    MERGE_REQUEST_PROJECT_PATH: str
    MERGE_REQUEST_PROJECT_URL: str
    MERGE_REQUEST_PROJECT_ID: int
    MERGE_REQUEST_LABELS: Optional[str]
    PIPE_GITLAB_USER_ID: int
    MERGE_REQUEST_TARGET_BRANCH_NAME: str
    MERGE_REQUEST_SOURCE_BRANCH_NAME: str

