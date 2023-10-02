# Сервис управления процессом Code Review.
### Компания Абсолют Банк 

Сервис автоматического назначения и контроля за проведением Code-Review.
Ответственный разработчик назначается случайно из пула доступных для команды reviewers в соответствии с конфигурацией команды.

Соответствующие уведомления отправляются в чат команды платформы Mattermost

Пример запроса:
```http
# Токен авторизации передается через Header **abtoken**
GET http://api.dev.a-fin.tech/tm/review?project_id={ID проекта в Gitlab}&mr_id={ID мердж-реквеста в контексте проекта}
```

Пример ответа:
```json
{
    "mr_id": 62,
    "mr_author": {
        "id": 3,
        "name": "Дмитрий Резниченко",
        "email": "drezn@a-fin.tech",
        "avatar_url": "https://git.a-fin.tech/uploads/-/system/user/avatar/3/avatar.png",
        "web_url": "https://git.a-fin.tech/reznichenko",
        "team": "green",
        "lead": "a.obedin",
        "username": "reznichenko"
    },
    "mr_reviewer": {
        "id": 43,
        "name": "Сергей Артемов",
        "email": "artemov@farzoom.com",
        "avatar_url": "https://secure.gravatar.com/avatar/276d57790f119eaad1b2e9106c756105?s=80&d=identicon",
        "web_url": "https://git.a-fin.tech/artemov",
        "team": "green",
        "lead": "a.obedin",
        "username": "artemov"
    },
    "created_at": "2023-01-25T16:46:51.364000+03:00",
    "updated_at": "2023-01-25T18:01:09.077000+03:00",
    "project_id": 408,
    "project_name": "farzoom/common/common-api-pi-proxy!62",
    "web_url": "https://git.a-fin.tech/farzoom/common/common-api-pi-proxy",
    "timestamp": "2023-01-25T17:54:09.158969"
}
```


### Конфигурация сервиса (ENV)
```dotenv
    # Обязательные:
    GITLAB_TOKEN=(token)
    GITLAB_URL=https://git.a-fin.tech
    MM_HOST=mm.a-fin.tech
    MM_TOKEN=(token)    
    SERVER_TOKEN=(token) 
    TEAM_CONFIG_PROJECT=farzoom/configs/team-config

    # Опциональные:
    MM_PORT=443 (default: 443)
    MM_BOT_MSG_INTERVAL=30 (default: 30)
    MM_GROUP_CHANNEL_ID='' (default: None)
    TEAM_CONFIG_FILE=team-config.yaml (default: team-config.yaml)
    TEAM_CONFIG_BRANCH=master (default: master)
    LOG_LEVEL=INFO (default: INFO)
    SERVER_ADDRESS=0.0.0.0 (default: 0.0.0.0)
    SERVER_PORT=8080 (default: 8080)
    SERVER_WORKERS=3 (default: 3)
    TEAM_CONFIG_UPDATE_INTERVAL=60 (default: 60)
    SENTRY_DSN=(dsn) (default: Null)
    SENTRY_TRACES_SAMPLE_RATE=1.0 (default: 1.0)
```

### Пример конфигурации команд (team-config.yaml):
```yaml
    teams:
      - team1:
          lead: user1
          members:
            - user1
            - user2
            - user3
          reviewers:
            - user1
            - user2
            - user6
      - team2:
            lead: user1
            members:
              - user5
              - user6
              - user7
            reviewers:
              - user1
              - user2
              - user6
              - user7
    projects:
      # Перечень проектов, которые попадаю в code-review при любых изменениях
      always:
        - farzoom/configs/afinance
      # Перечень проектов, исключены из code-review
      exclude:
        - farzoom/common/common-api-pi-proxy
      # Список файлов и расширений, изменения в которых будут игнорироваться
      skip:
        extensions:
          - bpmn
          - dmn
        files:
          - .gitlab-ci.yml
```