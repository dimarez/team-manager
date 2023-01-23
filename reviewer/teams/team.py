import random

from loguru import logger as log

from .git import Git
from .schemas import User, GitUser


class Team:
    _users: dict[str, User]
    _reviewers: dict[str: list[str]]
    git: Git

    def __init__(self, git: Git):
        self.git = git
        self._load_team_setup()

    def update_config(self):
        is_upd = self.git.load_config()
        if is_upd:
            self._load_team_setup()

    def _load_team_setup(self):
        team_setup = self.git.config
        users: {str: User} = {}
        ucache: list = []
        reviewers: dict = {}
        for team in team_setup["teams"]:
            for k, v in team.items():
                reviewers[k] = v["reviewers"]
                for member in v["members"]:
                    member = str(member).strip()
                    if member not in ucache:
                        udata: GitUser = self.git.get_user_data(username=member)
                        if udata:
                            udata.team = k
                            udata.lead = v["lead"]
                            udata.username = member
                            user = User.parse_obj(udata)
                            users[member] = user
                            ucache.append(member)
                for reviewer in v["reviewers"]:
                    reviewer = str(reviewer).strip()
                    if reviewer not in ucache:
                        udata: GitUser = self.git.get_user_data(username=reviewer)
                        if udata:
                            udata.team = k
                            udata.lead = v["lead"]
                            udata.username = reviewer
                            user = User.parse_obj(udata)
                            users[reviewer] = user
                            ucache.append(reviewer)
        ucache.clear()

        self._users = users
        self._reviewers = reviewers

    def get_random_reviewer_for_user(self, username: str) -> str | None:
        if username:
            user_team = self.get_team_by_user(username)
            if user_team:
                reviewer = self._get_random_reviewer_by_team(user_team, username)
                return reviewer
            else:
                log.error(f"Инициатор MR [{username}] не найден в списках команды")
                return None
        else:
            return None

    def get_user_id_by_name(self, name: str) -> (int, None):
        if name.strip():
            try:
                return self._users[name].id
            except KeyError:
                return None

    def get_user_name_by_id(self, id: int):
        if id:
            for key, value in self._users.items():
                if value.id == id:
                    return key
                return None
        else:
            return None

    def get_user_by_name(self, name: str) -> (User, None):
        if name.strip():
            try:
                user = self._users[name]
                return user
            except KeyError:
                return None

    def get_team_by_user(self, name: str) -> (str, None):
        if name.strip():
            try:
                team = self._users[name].team
                return team
            except KeyError:
                return None

    def get_reviewers_by_team(self, team: str) -> (int, None):
        if team.strip():
            try:
                id = self._reviewers[team]
                return id
            except KeyError:
                return None

    def _get_random_reviewer_by_team(self, team: str, cur_user: str) -> User | None:
        if team.strip() and cur_user.strip():
            try:
                reviewer = cur_user.strip()
                while reviewer.strip() == cur_user.strip():
                    reviewer = random.choice(self._reviewers[team])
                return self._users[reviewer]
            except KeyError:
                return None
