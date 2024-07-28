from .app import team, git
from .services import TeamService, GitService


async def get_team_service():
    return TeamService(team=team)


async def get_git_service():
    return GitService(git=git)
