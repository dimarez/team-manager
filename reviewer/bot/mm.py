from loguru import logger as log
from mattermostdriver import Driver
from mattermostdriver.exceptions import NoAccessTokenProvided, ResourceNotFound, InvalidOrMissingParameters
from requests.exceptions import ConnectionError

from reviewer.config import InitConfig
from reviewer.utilites import render_template
from .schemas import Config, MessageCodeReviewNotice, \
    MessageCodeReviewNoticeField, MsgTest


class Bot:
    _cfg: Config
    _link: Driver
    _bot_id: str

    def __init__(self, init_cfg: InitConfig):
        self._cfg = Config(url=init_cfg.MM_HOST, token=init_cfg.MM_TOKEN)
        self._link = Driver(self._cfg.dict())

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

    def find_user_by_email(self, email: str) -> dict | None:
        try:
            if email:
                user = self._link.users.get_user_by_email(email=email)
                return user
        except ResourceNotFound:
            log.warning(f"Пользователь с email: [{email}] не найден в каналах Mattermost")
            return None

    def _create_channel(self, user_id: str) -> str | None:
        try:
            channel = self._link.channels.create_direct_message_channel([self._bot_id, user_id])
            channel_id = channel["id"]
            if channel_id:
                return channel_id
        except InvalidOrMissingParameters as ex:
            log.error(f"Ошибка создания канала для пользователя -> [{ex}]")
            return None

    def generate_mr_notice(self) -> MessageCodeReviewNotice:
        test_data = MsgTest(project_path="farzoom/common/common-api-pi-proxy",
                            project_url='https://git.a-fin.tech/farzoom/common/common-api-pi-proxy')

        field_project = MessageCodeReviewNoticeField(
            short=False,
            title="Проект:",
            value=render_template('bot-msg-field-project.j2', test_data.dict())
        )

        print(field_project.dict())

    def send_private_message(self, email: str, text: str):
        try:
            user = self._link.users.get_user_by_email(email=email)
            if user:
                user_id = user["id"]
                user_login = user["username"]
                text = {"channel_id": f"{self._create_channel(user_id)}",
                        "props": {
                            "attachments": [
                                {
                                    "fallback": "Опа!",
                                    "color": "#FF8000",
                                    "text": f""":fire::fire::fire: \nПривет, @{user_login}! \n\nРады сообщить, что боги рандома избрали Тебя для проведения ревью кода любимого коллеги @drezn. :alarm3:\nМы очень расчитываем на тебя!""",
                                    'author_name': 'Review Bot',
                                    "author_icon": "https://mm.a-fin.tech/api/v4/users/pqqbmwtsai8fxcoudqehpwqkjc/image?_=1674196148597",
                                    "author_link": "https://mm.a-fin.tech/absolut-bank/channels/devel",
                                    "fields": [
                                        {
                                            "short": "false",
                                            "title": "Проект:",
                                            "value": "[farzoom/common/common-api-pi-proxy](https://git.a-fin.tech/farzoom/common/common-api-pi-proxy)\n[**DEVELOP**](https://git.a-fin.tech/farzoom/common/common-api-pi-proxy/-/tree/develop) :arrow_right: [**TEST-MR2**](https://git.a-fin.tech/farzoom/common/common-api-pi-proxy/-/tree/test-mr2)"
                                        },
                                        {
                                            "short": "True",
                                            "title": "Информация о MR:",
                                            "value": "id-58 [DEVELOP](https://git.a-fin.tech/farzoom/common/common-api-pi-proxy/-/merge_requests/59)"
                                        },
                                        {
                                            "short": "true",
                                            "title": "Diffs:",
                                            "value": "Количество [файлов](https://git.a-fin.tech/farzoom/common/common-api-pi-proxy/-/merge_requests/59/diffs) для ревью: [*8*]\nОбъем изменений: [**3000 байт**]"
                                        }
                                    ],
                                    "image_url": "https://mtlynch.io/human-code-reviews-1/flowchart.png"
                                }
                            ]
                        }}
                msg = self._link.posts.create_post(text)
                print(msg)
        except ResourceNotFound:
            log.warning(f"Адресат [{email}] не найден в каналах Mattermost")
        except InvalidOrMissingParameters as ex:
            log.error(f"Неверно заданы параметры -> [{ex}]")
