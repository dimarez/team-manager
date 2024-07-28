import random

import pydantic
from loguru import logger as log

from .git import Git
from .schemas import GitUser, Override, Group


class Team:
    _groups: dict[str, Group]
    _members: dict
    git: Git
    _overrides: list[Override]

    def __init__(self, git: Git):
        self.git = git
        self._load_team_config()
        self._load_override_config()

    def update_config(self):
        is_upd = self.git.load_config()
        if is_upd:
            self._load_team_config()
            self._load_override_config()

    def _load_override_config(self):
        project_setup = self.git.config["projects"]["override"]
        self._overrides = [self._create_override(name, val) for sets in project_setup for name, val in sets.items()]

    def _create_override(self, name, val):
        users = [self.git.get_user_data(username=rev) for rev in val["reviewers"]]
        try:
            over = Override(name=name,
                            quantity=val.get("quantity", 1),
                            components=val.get("components"),
                            reviewers=users)
        except Exception as e:
            log.error(f"Ошибка чтения override-блока конфигурации [{name}]. Блок будет пропущен! -> [{e}]")
            return None
        return over

    def _load_team_config(self):
        team_setup = self.git.config["teams"]
        self._members = self._load_users(team_setup)
        self._groups = self._load_teams(team_setup)

        log.debug(f"Результат загрузки пользователей из конфигурации: {self._members}")
        log.debug(f"Результат загрузки групп из конфигурации: {self._groups}")

    def _load_users(self, team_setup):
        users = {}
        for setup in team_setup:
            for team_name, team_info in setup.items():
                for member in team_info["members"]:
                    if member not in users:
                        user_data = self.git.get_user_data(username=member)
                        if user_data:
                            users[member] = {"team": team_name, "info": user_data}
        return users

    def _load_teams(self, team_setup):
        groups = {}
        for setup in team_setup:
            for team_name, team_info in setup.items():
                valid_reviewers = self._get_valid_reviewers(team_info["reviewers"])
                if valid_reviewers:
                    self._process_team(groups, team_name, team_info, valid_reviewers)
        return groups

    def _process_team(self, groups, team_name, team_info, valid_reviewers):
        try:
            lead = self.git.get_user_data(username=team_info.get("lead"))
            channel = team_info.get("channel")
            quantity = team_info.get("quantity") or 1
            assignee = self._get_assignee(team_info)

            group = Group(
                name=team_name,
                quantity=quantity,
                lead=lead,
                channel=channel,
                reviewers=valid_reviewers
            )

            if assignee:
                group.assignee = assignee

            groups[team_name] = group
        except pydantic.error_wrappers.ValidationError as e:
            log.error(
                f"Ошибка в чтении конфигурации на этапе парсинга команды [{team_name}]. Настройки команды не будут учтены! -> [{e}]"
            )

    def _get_assignee(self, team_info):
        assignee_username = team_info.get("assignee")
        return self.git.get_user_data(username=assignee_username) if assignee_username else None

    def _get_valid_reviewers(self, reviewers):
        valid_reviewers = []
        for reviewer in reviewers:
            reviewer_data = self.git.get_user_data(username=reviewer)
            if reviewer_data:
                valid_reviewers.append(reviewer_data)
            else:
                log.warning(f"Пользователь [{reviewer}] указан в конфигурации, но не найден в Gitlab!")
        return valid_reviewers

    def _check_project_for_override(self, project: str) -> tuple[bool, str] | tuple[bool, None]:
        for over in self._overrides:
            if project in over.components:
                return True, over.name
        return False, None

    def get_random_reviewer_for_user(self, username: str, project: str) -> list[GitUser] | None:

        res, over_group = self._check_project_for_override(project)

        if res:
            log.info(f"Проект [{project}] найден в исключениях! Ревьюверы будут выбраны из списков [{over_group}]")
            over_rev = self._get_random_reviewer_by_override_group(over_group, username)

            if not over_rev:
                log.error("Невозможно выбрать ревьювера. Нет доступных разработчиков")
                return None
            return over_rev

        if username:
            user = self.get_user_by_username(username)
            if not user:
                log.warning(f"Пользователь [{username}] не найден в конфигурации")
                return None
            reviewers = self._get_random_reviewer(user)
            return reviewers
        else:
            return None

    def _get_random_reviewer_by_override_group(self, over_group: str, cur_user: str) -> list[GitUser] | None:
        over_group = over_group.strip()
        cur_user = cur_user.strip()

        if not over_group or not cur_user:
            return None

        used_over = [over for over in self._overrides if over.name == over_group]
        available_reviewers = [reviewer for reviewer in used_over[0].reviewers if reviewer.uname != cur_user]

        if not available_reviewers:
            return None

        if len(available_reviewers) < used_over[0].quantity:
            log.warning(f"Количество ревьюверов [{used_over[0].quantity}] для исключения (override) [{used_over[0].name}] "
                        f"больше доступных пользователей [{len(available_reviewers)}]. Будет выбран один ревьювер!")

            reviewers = random.sample(available_reviewers, 1)
        else:
            reviewers = random.sample(available_reviewers, used_over[0].quantity)

        return [rev for rev in reviewers]

    def _get_random_reviewer(self, cur_user: dict) -> list[GitUser] | None:

        if not cur_user:
            return None

        available_reviewers: list[GitUser] = [reviewer for reviewer in self._groups[cur_user["team"]].reviewers if
                                              reviewer.uname != cur_user["info"].uname]

        if not available_reviewers:
            log.error("Невозможно выбрать ревьювера. Нет доступных разработчиков")
            return None

        quantity = self._groups[cur_user["team"]].quantity
        if len(available_reviewers) < quantity:
            log.warning(f"Количество ревьюверов [{quantity}] для команды [{cur_user['team']}] "
                        f"больше доступных пользователей [{len(available_reviewers)}]. Будет назначен один ревьювер!")

            r = random.sample(available_reviewers, 1)
        else:
            r = random.sample(available_reviewers, self._groups[cur_user["team"]].quantity)

        return [rev for rev in r]

    def get_user_by_username(self, name: str) -> dict | None:
        if name.strip():
            try:
                user = self._members[name]
                return user
            except KeyError:
                return None

    def get_team(self, name: str) -> Group | None:
        if name.strip():
            return self._groups[name]
        else:
            return None
