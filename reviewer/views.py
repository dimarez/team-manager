from fastapi import APIRouter, Depends, Query, HTTPException, Header
from gitlab.v4.objects import ProjectMergeRequest
from gitlab.v4.objects.projects import Project
from loguru import logger as log
from pydantic import Required

from .app import init_config
from .app_services import get_team_service, get_git_service
from .schemas import MrSetupAnswer
from .services import TeamService, GitService
from .teams.schemas import User

api_router = APIRouter()


@api_router.get('/review')
async def index(mr_id: int = Query(default=Required), project_id: int = Query(default=Required),
                team_service: TeamService = Depends(get_team_service),
                git_service: GitService = Depends(get_git_service),
                ABToken: str | None = Header(default=None)):
    if ABToken != init_config.SERVER_TOKEN:
        log.error("Ошибка авторизации!")  
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        log.info(f"Запрос на настрйоку код-ревью для MR {mr_id}, project {project_id}")
        mr: ProjectMergeRequest
        project: Project
        mr, project = git_service.get_mr(mr_id=mr_id, project_id=project_id)
        if mr:
            mr_ref = mr.references["full"]
            log.debug(mr)
            log.debug(project)
            if 'NoCodeReview' not in mr.labels:
                diffs = git_service.get_commit_info(mr)
                log.debug(diffs)
                if not git_service.check_project_exceptions(project.path_with_namespace) and diffs.count() > 0:
                    log.debug(f"По запрошенному MR с учетом фильтров найдено {diffs.count()} изменений")
                    reviewer: User = team_service.get_random_reviewer_for_user(mr.author["username"])
                    if reviewer:
                        log.info(f"Для MR [{mr_ref}] выбран ревьювер {reviewer}")
                        if git_service.set_mr_review_setting(reviewer, mr):
                            mr_answer = MrSetupAnswer(mr_id=mr_id,
                                                      author=team_service.get_user_by_name(mr.author['username']),
                                                      created_at=mr.created_at,
                                                      updated_at=mr.updated_at,
                                                      project_id=project_id,
                                                      project_name=project.path_with_namespace,
                                                      web_url=project.web_url,
                                                      reviewer=reviewer)
                            log.debug(mr_answer)
                            return mr_answer.dict()
                        else:
                            raise HTTPException(status_code=500, detail="Ошибка сохранения значений для MR")
                    else:
                        raise HTTPException(status_code=204, detail="Pass")
                else:
                    log.info(f"MR [{mr_ref}] пропущен в соответствии с действующими исключениями фильтрами")
                    raise HTTPException(status_code=204, detail="Pass")
            else:
                log.info(f"MR [{mr_ref}] пропущен в соответствии с действующими исключениями фильтрами")
                log.warning(f"Для MR {mr_id} в проекте {project_id} установлен флаг 'NoCodeReview'")
                raise HTTPException(status_code=204, detail="Pass")
        else:
            log.error("Ошибка загрузки MR")
            raise HTTPException(status_code=404, detail=f"MR {mr_id} в проекте {project_id} не найден")
