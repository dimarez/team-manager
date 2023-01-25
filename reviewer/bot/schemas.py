from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from reviewer.teams.schemas import User


class Config(BaseModel):
    url: str
    scheme: str = "https"
    token: str
    debug: bool = False
    port: int = 443
    request_timeout: int = 5
    basepath: str = "/api/v4"


class MessageCodeReviewNoticeField(BaseModel):
    short: bool
    title: str
    value: str


class MessageCodeReviewNoticeAttachment(BaseModel):
    fallback: str = "Опа!"
    color: str = "#FF8000"
    author_name: str = "Review Bot"
    author_icon: HttpUrl = "https://mm.a-fin.tech/api/v4/users/pqqbmwtsai8fxcoudqehpwqkjc/image?_=1674196148597"
    author_link: HttpUrl = "https://mm.a-fin.tech/absolut-bank/channels/devel"
    image_url: HttpUrl = "https://mtlynch.io/human-code-reviews-1/flowchart.png"
    text: str
    fields: list[MessageCodeReviewNoticeField]


class MessageCodeReviewNotice(BaseModel):
    channel_id: Optional[str]
    props: dict[str, list[MessageCodeReviewNoticeAttachment]]
