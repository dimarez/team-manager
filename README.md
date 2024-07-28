# Сервис управления процессом Code Review.

Сервис автоматического назначения и контроля за проведением Code-Review.
Ответственный разработчик назначается случайно из пула доступных для команды reviewers в соответствии с конфигурацией команды.

Соответствующие уведомления отправляются в чат команды платформы Mattermost

Пример запроса:
```http
# Токен авторизации передается через Header **apikey** (Если установлен параметр окружения AUTH_TOKEN)
GET http://url-to-service/review?project_id={ID проекта в Gitlab}&mr_id={ID мердж-реквеста в контексте проекта}
```

Пример ответа:
```json
{
    "mr_id": 2,
    "mr_author": {
        "id": 1101,
        "name": "Резниченко Дмитрий",
        "uname": "dmireznichenko",
        "avatar_url": "https://gitlab.tech.mvideo.ru/uploads/-/system/user/avatar/1101/avatar.png",
        "web_url": "https://gitlab.tech.mvideo.ru/dmireznichenko"
    },
    "mr_reviewer": {
        "id": 583,
        "name": "Гончаров Денис Юрьевич",
        "uname": "dengoncharov",
        "avatar_url": "https://secure.gravatar.com/avatar/7e0be92cc8be0fbd82d4ce1736f21d9ed7292ebeb3ccf589df2464af3c02c066?s=80&d=identicon",
        "web_url": "https://gitlab.tech.mvideo.ru/dengoncharov"
    },
    "created_at": "2024-07-28T06:59:06.684000+00:00",
    "updated_at": "2024-07-28T09:03:08.116000+00:00",
    "project_id": 4158,
    "project_name": "mvideoru/dbue/test!2",
    "review_channel": "rgmp1ca19pdktpn9efycace38r",
    "review_team": "group2",
    "review_lead": {
        "id": 583,
        "name": "Гончаров Денис Юрьевич",
        "uname": "dengoncharov",
        "avatar_url": "https://secure.gravatar.com/avatar/7e0be92cc8be0fbd82d4ce1736f21d9ed7292ebeb3ccf589df2464af3c02c066?s=80&d=identicon",
        "web_url": "https://gitlab.tech.mvideo.ru/dengoncharov"
    },
    "web_url": "https://gitlab.tech.mvideo.ru/mvideoru/dbue/test",
    "timestamp": "2024-07-28T12:03:02.606695"
}
```


### Конфигурация сервиса (ENV)
```dotenv
    # Обязательные:
    GITLAB_TOKEN=(token)
    GITLAB_URL=https://git.a-fin.tech
    MM_HOST=mm.a-fin.tech
    MM_TOKEN=(token)
    TEAM_CONFIG_PROJECT=farzoom/configs/team-config

    # Опциональные:
    AUTH_TOKEN=(token) (default: Null)
    MM_PORT=443 (default: 443)
    MM_BOT_MSG_INTERVAL=30 (default: 30)    
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
  - group1:
      lead: user
      channel: channel_id
      assignee: user
      members:
        - user1                
        - user2
        - user6
      reviewers:
        - user8
        - user1     
        - user6 
        - user10              
  - group2:
      lead: user
      members:
        - user11             
        - user10  
      reviewers:
        - user1
        - user2
        - user6        

projects:
  # Перечень проектов с фиксированными ревьюверами (игнорируются ревьюверы из группы)
  override:
    - core-mpa:  
        components: 
              - mvideoru/dbue/path
              - mvideoru/dbue/path2
        reviewers:
          - user1
          - user2
    - core-platform:
        components: 
              - mvideoru/dbue/shared-component
              - mvideoru/dbue/shared-component2
              - mvideoru/dbue/shared-component3
        reviewers:
          - user5
          - user6
      
  # Перечень проектов, исключены из code-review
  exclude:
    - mvideoru/dbue/exclude
    - mvideoru/dbue/exclude2
  # Список файлов и расширений, изменения в которых будут игнорироваться
  skip:
    extensions:
      - bpmn
      - dmn
    files:
      - .gitlab-ci.yml
```
