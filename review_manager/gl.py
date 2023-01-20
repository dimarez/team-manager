import gitlab
from gitlab.v4.objects import ProjectMergeRequest
import markdown

from .schema import Config, User, MrDiff
from loguru import logger as log

from pydantic import parse_obj_as

class MrGit:
    cfg: Config
    gl: gitlab.client.Gitlab
    mr: ProjectMergeRequest

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.gl = gitlab.Gitlab(url=cfg.CI_SERVER_URL, private_token=cfg.GITLAB_TOKEN)

    def get_mr(self):
        try:
            project = self.gl.projects.get(self.cfg.MERGE_REQUEST_PROJECT_ID, lazy=True)
            mr = project.mergerequests.get(self.cfg.MERGE_REQUEST_IID)
            if mr:
                self.mr = mr
                return mr
            else:
                return None
        except gitlab.exceptions.GitlabGetError:
            return None

    def get_commit_info(self):
        changes = self.mr.changes()
        for v in changes["changes"]:
            d: MrDiff = parse_obj_as(MrDiff, v)
            print(d.diff_size)

    def setup_mr_setting(self, reviewer: User, reviewer_username: str):
        # self.mr.assignee_ids = [reviewer.id]
        # self.mr.reviewer_ids = [reviewer.id]
        self.mr.assignee_ids = [3]
        self.mr.reviewer_ids = [3]
        self.mr.discussion_locked = True
        text = f"""Привет!
         
Данный MR был выбран для проведения обязательного ревью.         
Код будет проверен вашим коллегой @{reviewer_username}, о чем он/она были уведомлены в нашем чате.

Если продолжительное время нет реакции, советую обратиться на прямую или к вашему тимлиду @{reviewer.lead}
"""

        m = markdown.markdown(text)
        print(m)
        self.mr.discussions.create({'body': m})
        self.mr.save()
        log.info(f"Настройки для MR установлены")