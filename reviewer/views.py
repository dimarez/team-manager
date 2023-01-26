from fastapi import APIRouter, Depends, Query, HTTPException, Header
from gitlab.v4.objects import ProjectMergeRequest
from gitlab.v4.objects.projects import Project
from loguru import logger as log
from pydantic import Required
from starlette import status

from .app import init_config, msg_queue
from .app_services import get_team_service, get_git_service
from .schemas import MrSetupAnswer
from .services import TeamService, GitService
from .teams.schemas import User

api_router = APIRouter()


@api_router.get('/health', status_code=status.HTTP_200_OK)
def perform_healthcheck():
    return {'healthcheck': 'Everything OK!'}


@api_router.get('/review')
async def set_review(mr_id: int = Query(default=Required), project_id: int = Query(default=Required),
                     team_service: TeamService = Depends(get_team_service),
                     git_service: GitService = Depends(get_git_service),
                     abtoken: str | None = Header(default=None)):
    if abtoken != init_config.SERVER_TOKEN:
        log.error("Ошибка авторизации!")
        raise HTTPException(status_code=401, detail="Unauthorized")
    log.info(f"Получен запрос на настройку код-ревью для MR {mr_id}, project {project_id}")

    mr: ProjectMergeRequest
    project: Project
    mr, project = git_service.get_mr(mr_id=mr_id, project_id=project_id)

    if not mr:
        log.error("Ошибка загрузки MR")
        raise HTTPException(status_code=404, detail=f"MR {mr_id} в проекте {project_id} не найден")

    mr_ref = mr.references["full"]
    log.debug(mr)
    log.debug(project)

    if len(mr.reviewers) > 0:
        log.error("Повторный запрос на установку code-review пропущен")
        raise HTTPException(status_code=204, detail="Настройки code-review уже установлены")

    if 'NoCodeReview' in mr.labels:
        log.info(f"MR [{mr_ref}] пропущен в соответствии с действующими исключениями фильтрами")
        log.warning(f"Для MR {mr_id} в проекте {project_id} установлен флаг 'NoCodeReview'")
        raise HTTPException(status_code=204, detail="Pass")

    diffs = git_service.get_commit_info(mr)
    log.debug(diffs)
    # todo: перенести логику в сервис (проверка исключений)
    if git_service.check_project_exceptions(project.path_with_namespace) or diffs.count() == 0:
        log.info(f"MR [{mr_ref}] пропущен в соответствии с действующими исключениями фильтрами")
        raise HTTPException(status_code=204, detail="Pass")

    log.debug(f"По запрошенному MR с учетом фильтров найдено {diffs.count()} изменений")
    reviewer: User = team_service.get_random_reviewer_for_user(mr.author["username"])
    if not reviewer:
        raise HTTPException(status_code=204, detail="Pass")

    log.info(f"Для MR [{mr_ref}] выбран ревьювер {reviewer}")
    set_mr_setting_result = git_service.set_mr_review_setting(reviewer,
                                                              team_service.get_user_by_name(mr.author['username']), mr,
                                                              project, diffs)
    if not set_mr_setting_result:
        log.error("Ошибка сохранения значений для MR")
        raise HTTPException(status_code=500, detail="Ошибка сохранения значений для MR")

    log.debug(f"Result -> {set_mr_setting_result}")
    msg_queue.put(set_mr_setting_result)
    mr_answer = MrSetupAnswer.parse_obj(set_mr_setting_result)
    return mr_answer
