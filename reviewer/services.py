from .teams import Team, Git


class TeamService:
    def __init__(self, team):
        self.team: Team = team

    def get_team_by_user(self, name: str):
        return self.team.get_team_by_user(name)

    def get_random_reviewer_for_user(self, username: str):
        return self.team.get_random_reviewer_for_user(username)

    def get_user_by_name(self, name: str):
        return self.team.get_user_by_name(name)


class GitService:
    def __init__(self, git):
        self.git: Git = git

    def get_mr(self, project_id: int, mr_id: int):
        return self.git.get_mr_info(project_id, mr_id)

    def get_commit_info(self, mr):
        return self.git.get_commits_info(mr)

    def check_project_exceptions(self, project):
        return self.git.check_project_exceptions(project)

    def set_mr_review_setting(self, reviewer, author, mr, project, diffs):
        return self.git.set_mr_review_setting(reviewer, author, mr, project, diffs)
