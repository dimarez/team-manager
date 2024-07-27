import random
from typing import Tuple

from loguru import logger as log

from .git import Git
from .schemas import User, GitUser, Override, Group


class Team:
    _users: dict[str, User]
    _reviewers: dict[str: list[str]]


    _groups: dict
    _members: dict
    git: Git
    _overrides: list[Override]

    def __init__(self, git: Git):
        self.git = git
        self._load_team_setup()

        self._load_team_config()
        self._load_override_config()

    def update_config(self):
        is_upd = self.git.load_config()
        if is_upd:
            self._load_team_setup()

            self._load_team_config()
            self._load_override_config()

    def _load_override_config(self):
        project_setup = self.git.config["projects"]["override"]
        self._overrides = [self._create_override(name, val) for sets in project_setup for name, val in sets.items()]

    def _create_override(self, name, val):
        users = [self.git.get_user_data(username=rev) for rev in val["reviewers"]]
        return Override(name, components=val["components"], reviewers=users)

    def _load_team_setup(self):
        team_setup = self.git.config
        users: dict[str, User] = {}
        ucache: set = set()
        reviewers: dict = {}

        def process_user(member, team_name, lead):
            member = member.strip()
            if member not in ucache:
                udata: GitUser = self.git.get_user_data(username=member)
                if udata:
                    udata.team = team_name
                    udata.lead = lead
                    udata.username = member
                    user = User.parse_obj(udata)
                    users[member] = user
                    ucache.add(member)

        for team in team_setup["teams"]:
            for team_name, team_info in team.items():
                reviewers[team_name] = team_info["reviewers"]
                for member in team_info["members"]:
                    process_user(member, team_name, team_info["lead"])
                for reviewer in team_info["reviewers"]:
                    process_user(reviewer, team_name, team_info["lead"])

        self._users = users
        self._reviewers = reviewers

    def _load_team_config(self):
        team_setup = self.git.config["teams"]
        users = dict()
        group = dict()

        for setup in team_setup:
            for team_name, team_info in setup.items():
                for member in team_info["members"]:
                    if users.get(member) is None:
                        udata: GitUser = self.git.get_user_data(username=member)
                        if udata:
                            users[member] = {"team": team_name, "info": udata}

                rev = set(team_info["reviewers"])
                valid_rev: list[GitUser] = list()

                for r in rev:
                    udata: GitUser = self.git.get_user_data(username=r)
                    if udata:
                        valid_rev.append(udata)
                    else:
                        log.warning(f"Пользователь [{r}] указан в конфигурации, но не найден в Gitlab!")
                if len(valid_rev):
                    group[team_name] = Group(name=team_name, lead=team_info["lead"], channel=team_info["channel"], reviewers = valid_rev)

        self._members = users
        self._groups = group

        log.debug(f"Результат загрузки пользователей из конфигурации: [{self._members}]")
        log.debug(f"Результат загрузки групп из конфигурации: [{self._groups}]")

    def _check_project_for_override(self, project: str) -> tuple[bool, str] | tuple[bool, None]:
        for over in self._overrides:
            if project in over.components:
                return True, over.name
        return False, None

    def get_random_reviewer_for_user(self, username: str, project: str) -> User | None:

        res, group = self._check_project_for_override(project)

        if res:
            log.info(f"Проект [{project}] найден в исключениях! Ревьюверы будут выбраны из списков [{group}]")
            over_rev = self._get_random_reviewer_by_override_group(group, username)

            if not over_rev:
                log.error("Невозможно выбрать ревьювера. Нет доступных разработчиков")
                return None
            usr: User = self._get_user_by_name(username)

            return usr

        if username:
            user_team = self._get_team_by_user(username)
            if user_team:
                reviewer = self._get_random_reviewer_by_team(user_team, username)
                return reviewer
            else:
                log.error(f"Инициатор MR [{username}] не найден в списках команды")
                return None
        else:
            return None

    def _get_random_reviewer_by_override_group(self, group: str, cur_user: str) -> GitUser | None:
        group = group.strip()
        cur_user = cur_user.strip()

        if not group or not cur_user:
            return None

        used_over = [over for over in self._overrides if over.name == group]
        available_reviewers = [reviewer for reviewer in used_over[0].reviewers if reviewer.uname != cur_user]

        if not available_reviewers:
            return None

        reviewer = random.sample(available_reviewers, 1)[0]
        return reviewer



    def _get_random_reviewer_by_team(self, team: str, cur_user: str) -> User | None:
        team = team.strip()
        cur_user = cur_user.strip()

        if not team or not cur_user:
            return None

        if team not in self._reviewers or not self._reviewers[team]:
            return None

        available_reviewers = [reviewer for reviewer in self._reviewers[team] if reviewer != cur_user]

        if not available_reviewers:
            log.error("Невозможно выбрать ревьювера. Нет доступных разработчиков")
            return None

        reviewer = random.sample(available_reviewers, 1)[0]
        return self._users.get(reviewer)





    def _get_user_by_name(self, name: str) -> (GitUser, None):
        if name.strip():
            try:
                user = self._members[name]["info"]
                print(user)
                return user
            except KeyError:
                return None

    def _get_team_by_user(self, name: str) -> (str, None):
        if name.strip():
            try:
                team = self._members[name]["team"]
                return team
            except KeyError:
                return None
