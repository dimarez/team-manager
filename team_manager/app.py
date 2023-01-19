import logging
import os

import yaml
from .schema import Config
from .team import Team


def main():

    # # mr.description = 'New description'
    # # mr.assignee_ids = [3]
    # # mr.reviewer_ids = [3]
    # # mr.discussion_locked = True
    # # mr.discussions.create({'body': 'Старт процесса Code Review v2'})
    # # mr.save()
    with open('./afin-team-configuration.yaml', 'r') as file:
        setup = yaml.safe_load(file)
        cfg = Config.parse_obj(os.environ)
        teams = Team(setup, cfg)





