import gitlab
from gitlab.v4.objects import ProjectMergeRequest

from .schema import Config, User
from loguru import logger as log


class MrGit:
    cfg: Config
    gl: gitlab.client.Gitlab
    mr: ProjectMergeRequest

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.gl = gitlab.Gitlab(url=cfg.CI_SERVER_URL, private_token=cfg.GITLAB_TOKEN)

    # def get_user(self):
    #     user = self.gl.users.list(username="reznichenko")
    #     print(user[0])

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

    def setup_mr_setting(self, reviewer: User, reviewer_username: str):
        # self.mr.assignee_ids = [reviewer.id]
        # self.mr.reviewer_ids = [reviewer.id]
        self.mr.assignee_ids = [3]
        self.mr.reviewer_ids = [3]
        self.mr.discussion_locked = True
        self.mr.discussions.create({'body': f'Старт процесса Code Review v2. Возрадуйся @{reviewer_username}'})
        self.mr.save()
        log.info(f"Настройки для MR установлены")