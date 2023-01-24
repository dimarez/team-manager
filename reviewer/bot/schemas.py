from pydantic import BaseModel, HttpUrl


class Config(BaseModel):
    url: str
    scheme: str = "https"
    token: str
    debug: bool = False
    port: int = 443
    request_timeout: int = 5
    basepath: str = "/api/v4"


class MessageTemplateRenderData(BaseModel):
    project_name: str
    web_url: HttpUrl
    branch_src: str
    branch_src_link: HttpUrl
    branch_dst: str
    branch_dst_link: HttpUrl
    mr_reviewer: str
    mr_author: str
    mr_id: str
    mr_url: HttpUrl
    mr_name: str
    mr_diffs: str
    diff_url: HttpUrl
    diff_count: int
    diff_bytes: int


class MsgTest(BaseModel):
    project_path: str
    project_url: HttpUrl


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
    channel_id: str = "asdas"
    props: dict[str, list[MessageCodeReviewNoticeAttachment]]
