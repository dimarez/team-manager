from gitlab.v4.objects import ProjectMergeRequest, Project

from .teams import Team, Git
from .teams.schemas import GitUser, MrDiffList, Group


class TeamService:
    def __init__(self, team):
        self.team: Team = team

    def get_team(self, name: str):
        return self.team.get_team(name)

    def get_random_reviewer_for_user(self, username: str, project: str) -> GitUser:
        return self.team.get_random_reviewer_for_user(username, project)

    def get_user_by_username(self, name: str) -> dict:
        return self.team.get_user_by_username(name)


class GitService:
    def __init__(self, git):
        self.git: Git = git

    def get_mr(self, project_id: int, mr_id: int):
        return self.git.get_mr_info(project_id, mr_id)

    def get_commit_info(self, mr):
        return self.git.get_commits_info(mr)

    def check_project_exceptions(self, project):
        return self.git.check_project_exceptions(project)

    def set_mr_review_setting(self, reviewer: GitUser,
                              author: GitUser,
                              team: Group,
                              mr: ProjectMergeRequest,
                              project: Project,
                              diffs: MrDiffList):
        return self.git.set_mr_review_setting(reviewer, author, team, mr, project, diffs)
