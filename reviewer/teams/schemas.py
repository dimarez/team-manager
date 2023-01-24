from typing import Optional

from pydantic import BaseModel, Extra, EmailStr


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
