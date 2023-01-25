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
from .schemas import GitUser, MrDiffList, MrDiff, User, MrCrResultData
from reviewer.utilites import render_template

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
            _config_sha256 = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE, ref=self.cfg.TEAM_CONFIG_BRANCH).content_sha256
            if _config_sha256 != self._config_sha256:
                if self._config_sha256:
                    log.warning("Обнаружена свежая версия конфига. Загружаем!")
                config_encoded = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE, ref=self.cfg.TEAM_CONFIG_BRANCH).content
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

    def set_mr_review_setting(self,
                              reviewer: User,
                              author: User,
                              mr: ProjectMergeRequest,
                              project: gitlab.v4.objects.projects.Project,
                              diffs: MrDiffList) -> MrCrResultData | None:

        # mr.assignee_ids = [reviewer.id]
        # mr.reviewer_ids = [reviewer.id]
        mr.assignee_ids = [3]
        mr.reviewer_ids = [3]

        mr.discussion_locked = True

        text = render_template('git-mr-thread-body.j2', {"mr_author_username": mr.author["username"],
                                                         "mr_web_url": mr.web_url,
                                                         "reviewer_username": reviewer.username,
                                                         "reviewer_lead": reviewer.lead})
        mr.discussions.create({'body': text})
        mr.save()
        #if mr.assignee['id'] == reviewer.id:
        if mr.assignee['id'] == 3:
            log.info(f"Настройки для MR {mr.references['full']} установлены")

            mr_cr_result: MrCrResultData = MrCrResultData(
                project_name=mr.references['full'],
                project_id=project.id,
                web_url=project.web_url,
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                mr_reviewer=reviewer,
                mr_reviewer_avatar=mr.assignee["avatar_url"],
                mr_reviewer_url=mr.assignee["web_url"],
                mr_author=author,
                mr_author_avatar=mr.author["avatar_url"],
                mr_author_url=mr.author["web_url"],
                mr_id=mr.iid,
                mr_url=mr.web_url,
                mr_title=mr.title,
                mr_diffs=diffs,
                created_at=mr.created_at,
                updated_at=mr.updated_at
            )
            return mr_cr_result
        else:
            log.error(f"Ошибка установки значений code-review для MR [{mr.references['full']}. "
                      f"Итоговое значение assignee_ids не соответствует устанавливаемому")
            return None
