# Сервис управления процессом code-review

Заглушка

## Конфигурация сервиса (ENV)

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