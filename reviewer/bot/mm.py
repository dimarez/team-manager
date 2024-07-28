from loguru import logger as log
from mattermostdriver import Driver
from mattermostdriver.exceptions import NoAccessTokenProvided, ResourceNotFound, InvalidOrMissingParameters
from requests.exceptions import ConnectionError

from reviewer.config import InitConfig
from reviewer.teams.schemas import MrCrResultData
from reviewer.utilites import render_template
from .schemas import Config, MessageCodeReviewNotice, \
    MessageCodeReviewNoticeField, MessageCodeReviewNoticeAttachment


class Bot:
    _cfg: Config
    _link: Driver
    _bot_id: str
    _init_cfg: InitConfig

    def __init__(self, init_cfg: InitConfig):
        self._cfg = Config(url=init_cfg.MM_HOST, token=init_cfg.MM_TOKEN)
        self._link = Driver(self._cfg.dict())
        self._init_cfg = init_cfg
        self._connect()

    def _connect(self) -> dict | None:
        try:
            resp = self._link.login()
            if resp:
                log.debug(resp)
                self._bot_id = resp['id']
                return resp
        except ConnectionError as ex:
            log.error(f"Ошибка подключения к Mattermost -> [{ex}]")
            return None
        except NoAccessTokenProvided as ex:
            log.error(f"Ошибка авторизации в Mattermost -> [{ex}]")
            return None

    def get_user_by_email(self, email: str) -> dict | None:
        try:
            if email:
                user = self._link.users.get_user_by_email(email=email)
                return user
        except ResourceNotFound:
            log.warning(f"Пользователь с email: [{email}] не найден в каналах Mattermost")
            return None

    def get_user_by_username(self, username: str) -> dict | None:
        try:
            if username:
                user = self._link.users.get_user_by_username(username)
                return user
        except ResourceNotFound:
            log.warning(f"Пользователь с username: [{username}] не найден в каналах Mattermost")
            return None

    def _create_private_channel(self, user_id: str) -> str | None:
        try:
            channel = self._link.channels.create_direct_message_channel([self._bot_id, user_id])
            channel_id = channel["id"]
            if channel_id:
                return channel_id
        except InvalidOrMissingParameters as ex:
            log.error(f"Ошибка создания канала для пользователя -> [{ex}]")
            return None

    def send_private_message(self, username: str, text: str) -> str | None:
        try:
            user = self.get_user_by_username(username)
            if user:
                user_id = user["id"]
                channel_id = self._create_private_channel(user_id)
                if channel_id:
                    return self._link.posts.create_post({"channel_id": channel_id,
                                                         "message": text})
                else:
                    return None
            else:
                return None
        except ResourceNotFound:
            log.warning(f"Адресат [{username}] не найден в каналах Mattermost")
        except InvalidOrMissingParameters as ex:
            log.error(f"Неверно заданы параметры -> [{ex}]")

    def send_group_message(self, queue_mr_result: MrCrResultData):
        tmpl_variables = {
            "mr_reviewer_username": self.get_user_by_username(queue_mr_result.mr_reviewer.uname)["username"],
            "mr_author_username": self.get_user_by_username(queue_mr_result.mr_author.uname)["username"],
            "mr_url": queue_mr_result.mr_url,
            "project_name": queue_mr_result.project_name,
        }

        if queue_mr_result.mr_assignee:
            tmpl_variables["mr_assignee_username"] = self.get_user_by_username(queue_mr_result.mr_assignee.uname)["username"]

        msg = render_template('bot-msg-group.j2', tmpl_variables)
        self._link.posts.create_post({"channel_id": queue_mr_result.review_channel, "message": msg})

    def send_mr_notice_message(self, queue_mr_result: MrCrResultData) -> dict | None:
        try:
            if self._init_cfg.DEBUG_REVIEWER_USERNAME:
                user_name = self._init_cfg.DEBUG_REVIEWER_USERNAME
            else:
                user_name = queue_mr_result.mr_reviewer.uname
            user = self.get_user_by_username(user_name)
            if user:
                user_id = user["id"]
                channel_id = self._create_private_channel(user_id)
                notice = self._generate_mr_notice(queue_mr_result)
                if notice:
                    notice.channel_id = channel_id
                    msg = self._link.posts.create_post(notice.dict())
                    return msg
                else:
                    return None
        except ResourceNotFound:
            log.warning(f"Адресат [{queue_mr_result.mr_reviewer.uname}] не найден в каналах Mattermost")
            return None
        except InvalidOrMissingParameters as ex:
            log.error(f"Неверно заданы параметры -> [{ex}]")
            return None

    def _generate_mr_notice(self, set_mr_setting_result: MrCrResultData) -> MessageCodeReviewNotice | None:

        try:
            fields = []
            diff_variables = {"diff_url": set_mr_setting_result.diff_url,
                              "diff_count": set_mr_setting_result.mr_diffs.count(),
                              "diff_bytes": set_mr_setting_result.mr_diffs.sum_diff_scope(),
                              "diffs": set_mr_setting_result.mr_diffs.diffs}

            field_diffs = MessageCodeReviewNoticeField(
                short=False,
                title="Diffs:",
                value=render_template('bot-msg-field-diffs.j2', diff_variables)
            )
            fields.append(field_diffs.dict())

            field_mr = MessageCodeReviewNoticeField(
                short=False,
                title="Информация о MR:",
                value=render_template('bot-msg-field-mr.j2', set_mr_setting_result.dict())
            )
            fields.append(field_mr.dict())

            msg_attachments = []
            attachment_variables = {
                "mr_reviewer_username": self.get_user_by_username(set_mr_setting_result.mr_reviewer.uname)["username"],
                "mr_author_username": self.get_user_by_username(set_mr_setting_result.mr_author.uname)["username"],
                "mr_url": set_mr_setting_result.mr_url}
            msg_attachments.append(
                MessageCodeReviewNoticeAttachment(text=render_template('bot-msg-text.j2', attachment_variables),
                                                  fields=fields))

            msg_notice = MessageCodeReviewNotice(props={"attachments": msg_attachments})
            return msg_notice

        except Exception as ex:
            log.error(f"Ошибка генерации сообщения для бота -> {ex}")
            return None
