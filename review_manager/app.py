from loguru import logger as log
import os

import yaml
from .schema import Config, User
from .team import Team
from .gl import MrGit

def main():

    # # mr.assignee_ids = [3]
    # # mr.reviewer_ids = [3]
    # # mr.discussion_locked = True
    # # mr.discussions.create({'body': 'Старт процесса Code Review v2'})
    # # mr.save()
    with open('./afin-team-configuration.yaml', 'r') as file:
        setup = yaml.safe_load(file)
        cfg: Config = Config.parse_obj(os.environ)

        mrg = MrGit(cfg)
        mr = mrg.get_mr()
        if mr:
            try:
                excl_project = setup["projects"]["exclude"]
            except KeyError:
                excl_project = None

            if excl_project is None or cfg.MERGE_REQUEST_PROJECT_PATH not in excl_project:
                if "NoCodeReview" not in cfg.MERGE_REQUEST_LABELS.split(','):
                    team = Team(setup, cfg)
                    username = team.get_user_name_by_id(cfg.PIPE_GITLAB_USER_ID)
                    rand_reviewer = team.get_random_reviewer_by_team(team.get_team_by_user(username), username)
                    reviewer: User = team.get_user_by_name(rand_reviewer)
                    log.info(f"Для MR {cfg.MERGE_REQUEST_IID} выбран ревьювер {reviewer.name}")
                    mrg.setup_mr_setting(reviewer, rand_reviewer)


                else:
                    log.warning("Задана метка NoCodeReview. Ревью не будет назначено!")
            else:
                log.warning(f"Проект {cfg.MERGE_REQUEST_PROJECT_PATH} в списке исключений. Ревью не будет назначено!")
        else:
            log.error("MR не найден!")





