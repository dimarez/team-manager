import base64
import sys

import gitlab
import yaml
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError
from gitlab.v4.objects import ProjectMergeRequest
from loguru import logger as log
from pydantic import parse_obj_as
from yaml.scanner import ScannerError

from reviewer.config import InitConfig
from .schemas import GitUser, MrDiffList, MrDiff, User


class Git:
    init_cfg: InitConfig
    gl: gitlab.client.Gitlab
    config: dict
    _config_sha256: str = ""

    def __init__(self, init_cfg: InitConfig):
        self.cfg = init_cfg
        self.gl: gitlab.client.Gitlab = gitlab.Gitlab(url=init_cfg.GITLAB_URL, private_token=init_cfg.GITLAB_TOKEN)
        try:
            self.gl.auth()
            log.info(f"Модуль успешно подключен к {init_cfg.GITLAB_URL}")
            self.load_config()
        except (GitlabAuthenticationError, Exception) as ex:
            log.error(f"Ошибка подключения к ресурсу {init_cfg.GITLAB_URL} -> [{ex}]")
            sys.exit()

    def load_config(self) -> bool:
        project = self.gl.projects.get(self.cfg.TEAM_CONFIG_PROJECT)
        try:
            _config_sha256 = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE, ref="master").content_sha256
            if _config_sha256 != self._config_sha256:
                if self._config_sha256:
                    log.warning("Обнаружена свежая версия конфига. Загружаем!")
                config_encoded = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE, ref="master").content
                config_decoded = base64.b64decode(config_encoded).decode()
                self.config = yaml.safe_load(config_decoded)
                self._config_sha256 = _config_sha256
                log.info("Конфигурация успешно загружена")
                log.debug(self.config)
                return True
            else:
                return False
        except (GitlabGetError, ScannerError) as ex:
            log.error(
                f"Ошибка загрузки файла командной конфигурации ({self.cfg.TEAM_CONFIG_FILE}) в проекте "
                f"{self.cfg.GITLAB_URL}/{self.cfg.TEAM_CONFIG_PROJECT} -> [{ex}]")

    def get_user_data(self, username: str) -> GitUser | None:
        user = self.gl.users.list(username=username.strip())
        if user and user[0].state == "active":
            udata = GitUser(id=user[0].id,
                            name=user[0].name,
                            avatar_url=user[0].avatar_url,
                            web_url=user[0].web_url,
                            email=user[0].email)
            return udata
        else:
            return None

    def check_project_exceptions(self, project) -> bool:
        try:
            exclude_project_option = self.config["projects"]["exclude"]
        except KeyError:
            exclude_project_option = None
        if exclude_project_option is None or project not in exclude_project_option:
            return False
        else:
            return True

    def get_mr_info(self, project_id: int, mr_id: int) -> [ProjectMergeRequest | None,
                                                           gitlab.v4.objects.projects.Project | None]:
        try:
            project: gitlab.v4.objects.projects.Project = self.gl.projects.get(project_id, lazy=False)
            mr: ProjectMergeRequest = project.mergerequests.get(mr_id)
            if mr and mr.state != "closed":
                return mr, project
            else:
                return None, None
        except gitlab.exceptions.GitlabGetError:
            return None, None

    def get_commits_info(self, mr: ProjectMergeRequest) -> MrDiffList:
        changes = mr.changes()
        diffs = MrDiffList()
        for v in changes["changes"]:
            d: MrDiff = parse_obj_as(MrDiff, v)
            diffs.append(d, self.config["projects"]["skip"])
        return diffs

    def set_mr_review_setting(self, reviewer: User, mr: ProjectMergeRequest) -> bool:
        mr.assignee_ids = [reviewer.id]
        mr.reviewer_ids = [reviewer.id]
        mr.discussion_locked = True
        text = f"""Привет @{mr.author["username"]}!

Данный [MR]({mr.web_url}) был выбран для проведения **обязательного** ревью. Надеюсь, ты так же рад(а), как и мы!
Твоим кодом будет восторгаться @{reviewer.username}, о чем мы незамедлительно сообщим в чате.

Если продолжительное время нет реакции, советую обратиться [напрямую](https://mm.a-fin.tech) или к вашему тимлиду @{reviewer.lead}
Желаем удачи!"""
        mr.discussions.create({'body': text})
        mr.save()
        if mr.assignee['id'] == reviewer.id:
            log.info(f"Настройки для MR установлены")
            return True
        else:
            log.error(f"Ошибка установки значений code-review для MR [{mr.references['full']}. "
                      f"Итоговое значение assignee_ids не соответствует устанавливаемому")
            return False
