import base64
import sys

import gitlab
import yaml
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError, GitlabCreateError
from gitlab.v4.objects import ProjectMergeRequest
from loguru import logger as log
from pydantic import parse_obj_as
from yaml.scanner import ScannerError

from reviewer.config import InitConfig
from reviewer.utilites import render_template
from .schemas import GitUser, MrDiffList, MrDiff, MrCrResultData, Group


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
            _config_sha256 = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE,
                                               ref=self.cfg.TEAM_CONFIG_BRANCH).content_sha256
            if _config_sha256 != self._config_sha256:
                if self._config_sha256:
                    log.warning("Обнаружена свежая версия конфига. Загружаем!")
                config_encoded = project.files.get(file_path=self.cfg.TEAM_CONFIG_FILE,
                                                   ref=self.cfg.TEAM_CONFIG_BRANCH).content
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
        if not username:
            return None
        user = self.gl.users.list(username=username.strip())

        if user and user[0].state == "active":
            udata = GitUser(id=user[0].id,
                            name=user[0].name,
                            uname=user[0].username,
                            avatar_url=user[0].avatar_url,
                            web_url=user[0].web_url)
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

    def set_mr_review_setting(
            self,
            reviewers: list[GitUser],
            author: GitUser,
            team: Group,
            mr: ProjectMergeRequest,
            project: gitlab.v4.objects.projects.Project,
            diffs: MrDiffList
    ) -> MrCrResultData | None:

        def assign_reviewers_and_assignees():
            """Назначает ревьюеров и ответственных в зависимости от конфигурации и команды."""
            if self.cfg.DEBUG_REVIEWER_ID:
                mr.assignee_ids = [self.cfg.DEBUG_REVIEWER_ID]
                mr.reviewer_ids = [self.cfg.DEBUG_REVIEWER_ID]
            else:
                if team.assignee:
                    log.info(
                        f"Для команды [{team.name}] установлен фиксированный ответственный (assignee) [{team.assignee.name} ({team.assignee.uname})]")
                    mr.assignee_ids = [team.assignee.id]
                elif reviewers:
                    mr.assignee_ids = [reviewers[0].id]
                else:
                    log.error("Список ревьюеров пуст")
                    return False
                mr.reviewer_ids = [rev.id for rev in reviewers]
            return True

        def create_discussion_threads():
            """Создает обсуждения для каждого ревьюера."""
            for reviewer in reviewers:
                ctx = {
                    "mr_author_username": mr.author["username"],
                    "mr_web_url": mr.web_url,
                    "reviewer_username": reviewer.uname,
                    "reviewer_lead": team.lead.uname if team.lead else None
                }
                text = render_template('git-mr-thread-body.j2', ctx)
                discussion = mr.discussions.create({'body': text})
                if discussion:
                    reviewer.thread_id = discussion.attributes['notes'][0]["id"]

        def build_mr_cr_result_data():
            """Формирует данные результата для MR."""
            return MrCrResultData(
                review_team=team.name,
                review_lead=team.lead,
                review_channel=team.channel,
                project_name=mr.references['full'],
                project_id=project.id,
                web_url=project.web_url,
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                mr_reviewers=reviewers,
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
                updated_at=mr.updated_at,
                mr_assignee=team.assignee if team.assignee else None
            )

        try:
            if not assign_reviewers_and_assignees():
                return None

            mr.discussion_locked = False

            create_discussion_threads()

            res = mr.save()

            if res:
                log.info(f"Настройки для MR {mr.references['full']} установлены")
                return build_mr_cr_result_data()
            else:
                log.error(f"Ошибка установки значений code-review для MR [{mr.references['full']}]. "
                          f"Итоговое значение assignee_ids не соответствует устанавливаемому")
                return None

        except GitlabCreateError as ex:
            log.exception(f"Ошибка сохранения настроек MR для ревью -> [{ex}]")
            return None
        except Exception as ex:
            log.exception(ex)
            return None