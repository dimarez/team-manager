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


# - echo ${PIPE_GITLAB_USER_ID}
#       - echo ${MERGE_REQUEST_ID}
#       - echo ${MERGE_REQUEST_IID}
#       - echo ${MERGE_REQUEST_PROJECT_PATH}
#       - echo ${MERGE_REQUEST_PROJECT_ID}
#       - echo ${MERGE_REQUEST_LABELS}
#       - echo ${CI_PIPELINE_SOURCE}
#       - echo ${MERGE_REQUEST_TARGET_BRANCH_NAME}
#       - echo ${PIPELINE_JOB}


class Config(BaseModel):
    GITLAB_TOKEN: str
    GITLAB_URL: str
    MERGE_REQUEST_IID: Optional[str]
    MERGE_REQUEST_PROJECT_PATH: Optional[str]
    MERGE_REQUEST_LABELS: Optional[str]
    PIPE_GITLAB_USER_ID: Optional[str]
