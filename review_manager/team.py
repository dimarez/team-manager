from typing import Union
import gitlab
from .schema import User
from loguru import logger as log
import random


class Team:
    _users: dict[str, User]
    _reviewers: dict[str: list[str]]
    _GITLAB_TOKEN: str
    _GITLAB_URL: str

    def __init__(self, setup, config):
        self._GITLAB_URL = config.CI_SERVER_URL
        self._GITLAB_TOKEN = config.GITLAB_TOKEN
        self._users, self._reviewers = create_users_list(setup, self._GITLAB_TOKEN, self._GITLAB_URL)

    def get_user_id_by_name(self, name: str) -> [int, None]:
        if name.strip():
            try:
                id = self._users[name].id
                return id
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

    def get_user_by_name(self, name: str) -> [User, None]:
        if name.strip():
            try:
                user = self._users[name]
                return user
            except KeyError:
                return None

    def get_team_by_user(self, name: str) -> [str, None]:
        if name.strip():
            try:
                team = self._users[name].team
                return team
            except KeyError:
                return None

    def get_reviewers_by_team(self, team: str) -> [int, None]:
        if team.strip():
            try:
                id = self._reviewers[team]
                return id
            except KeyError:
                return None

    def get_random_reviewer_by_team(self, team: str, cur_user: str) -> [str, None]:
        if team.strip() and cur_user.strip():
            try:
                reviewer = cur_user.strip()
                while reviewer.strip() == cur_user.strip():
                    reviewer = random.choice(self._reviewers[team])
                return reviewer
            except KeyError:
                return None


def create_users_list(configuration, gitlab_token, gitlab_url) -> tuple[dict[str, User], dict]:
    gl = gitlab.Gitlab(url=gitlab_url, private_token=gitlab_token)
    gl.auth()
    users: {str: User} = {}
    ucache: list = []
    reviewers: dict = {}
    for team in configuration["teams"]:
        for k, v in team.items():
            reviewers[k] = v["reviewers"]
            for member in v["members"]:
                member = str(member).strip()
                if member not in ucache:
                    udata = gitlab_get_user_data(username=member, link=gl, lead=v["lead"], team=k)
                    if udata:
                        users[member] = udata
                        ucache.append(member)
            for reviewer in v["reviewers"]:
                reviewer = str(reviewer).strip()
                if reviewer not in ucache:
                    udata = gitlab_get_user_data(username=reviewer, link=gl, lead=v["lead"], team=k)
                    if udata:
                        users[reviewer] = udata
                        ucache.append(reviewer)
    ucache.clear()
    gl.session.close()
    return users, reviewers


def gitlab_get_user_data(username: str, link: gitlab.client.Gitlab, team: str, lead: str) -> Union[User, None]:
    user = link.users.list(username=username.strip())
    if user and user[0].state == "active":
        U = user[0]
        email = U.emails.list()
        udata = User(id=U.id,
                     name=U.name,
                     avatar_url=U.avatar_url,
                     web_url=U.web_url,
                     email=email[0].email,
                     lead=lead,
                     team=team)
        return udata
    else:
        log.warning(f"Пользователь {username} задан в конфигурации, но не найден в gitlab (активные учетки)")
        return None
