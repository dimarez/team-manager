from loguru import logger as log
import os

import yaml
from .schema import Config, User
from .team import Team
from .gl import MrGit


def main():
    with open('./afin-team-configuration.yaml', 'r') as file:
        setup = yaml.safe_load(file)
        cfg: Config = Config.parse_obj(os.environ)
        cfg.MERGE_REQUEST_URL = f"{cfg.CI_SERVER_URL}/{cfg.MERGE_REQUEST_PROJECT_PATH}/-/merge_requests/{cfg.MERGE_REQUEST_IID}"

        mrg = MrGit(cfg)
        mr = mrg.get_mr()
        if mr:
            try:
                exclude_project_option = setup["projects"]["exclude"]
            except KeyError:
                exclude_project_option = None

            if exclude_project_option is None or cfg.MERGE_REQUEST_PROJECT_PATH not in exclude_project_option:
                if "NoCodeReview" not in cfg.MERGE_REQUEST_LABELS.split(','):
                    team = Team(setup, cfg)
                    username = team.get_user_name_by_id(cfg.PIPE_GITLAB_USER_ID)
                    user_team = team.get_team_by_user(username)
                    rand_reviewer_username = team.get_random_reviewer_by_team(user_team, username)
                    reviewer: User = team.get_user_by_name(rand_reviewer_username)
                    log.info(f"Для MR {cfg.MERGE_REQUEST_IID} выбран ревьювер {reviewer.name}")
                    mrg.setup_mr_setting(reviewer, rand_reviewer_username)
                else:
                    log.warning("Задана метка NoCodeReview. Ревью не будет назначено!")
                    # todo: сообщить лиду в mattermost
            else:
                log.warning(f"Проект {cfg.MERGE_REQUEST_PROJECT_PATH} в списке исключений. Ревью не будет назначено!")
        else:
            log.error("MR не найден!")





