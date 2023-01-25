from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Extra, EmailStr, HttpUrl, root_validator


class GitUser(BaseModel):
    id: int
    name: Optional[str]
    email: EmailStr
    avatar_url: Optional[str]
    web_url: Optional[str]

    class Config:
        extra = Extra.allow


class User(GitUser):
    team: str
    lead: str
    username: str


class MrInfo(BaseModel):
    author: dict


class MrDiff(BaseModel):
    diff: str
    new_path: str
    diff_size: Optional[int]

    def __init__(self, **data):
        super().__init__(**data)
        self.diff_size = len(self.diff)


class MrDiffList(BaseModel):
    diffs: list[MrDiff] = []

    def count(self) -> int:
        return len(self.diffs)

    def sum_diff_scope(self) -> int:
        scope = 0
        for diff in self.diffs:
            scope += diff.diff_size
        return scope

    def append(self, item: MrDiff, skip: dict):
        skip_extensions = tuple(skip["extensions"])
        skip_files = tuple(skip["files"])
        if not item.new_path.lower().endswith(skip_extensions) and item.new_path.lower() not in skip_files:
            self.diffs.append(item)


class MrCrResultData(BaseModel):
    project_name: str
    project_id: int
    web_url: HttpUrl
    source_branch: str
    source_branch_link: Optional[HttpUrl]
    target_branch: str
    target_branch_link: Optional[HttpUrl]
    mr_reviewer: User
    mr_reviewer_avatar: HttpUrl
    mr_reviewer_url: HttpUrl
    mr_author: User
    mr_author_avatar: HttpUrl
    mr_author_url: HttpUrl
    mr_id: str
    mr_url: HttpUrl
    mr_title: str
    mr_diffs: MrDiffList
    diff_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime

    @root_validator
    def set_links(cls, values):
        values['source_branch_link'] = f"{values.get('web_url')}/-/tree/{values.get('source_branch')}"
        values['target_branch_link'] = f"{values.get('web_url')}/-/tree/{values.get('target_branch')}"
        values['diff_url'] = f"{values.get('mr_url')}/diffs"
        return values
