## Сервис управления процессом code-review

Сервис автоматического назначения и контроля за проведением Code-Review.
Ответственный разработчик назначается случайно в соответствии с конфигурацией команды.

Соответствующие уведомления отправляются в чат команды платформы Mattermost

Пример запроса:
```http request
   ### Expect { message: 'Wellcome to TestsAPI'}
   GET http://api.dev.a-fin.tech/tm/review?project_id={ID проекта в Gitlab}&mr_id={ID мердж-реквеста в контексте проекта}
```
Токен авторизации передается через Header **abtoken**


### Конфигурация сервиса (ENV)
```ini
    Обязательные:
    GITLAB_TOKEN=(token)
    GITLAB_URL=https://git.a-fin.tech
    MM_HOST=mm.a-fin.tech
    MM_TOKEN=(token)
    MM_BOT_MSG_INTERVAL=30
    SERVER_TOKEN=(token) 
    TEAM_CONFIG_PROJECT=farzoom/configs/team-config

    Опциональные:
    MM_PORT=443 (default: 443)
    MM_BOT_MSG_INTERVAL=30 (default: 30)
    TEAM_CONFIG_FILE=team-config.yaml (default: team-config.yaml)
    TEAM_CONFIG_BRANCH=master (default: master)
    LOG_LEVEL=INFO (default: INFO)
    SERVER_ADDRESS=0.0.0.0 (default: 0.0.0.0)
    SERVER_PORT=8080 (default: 8080)
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