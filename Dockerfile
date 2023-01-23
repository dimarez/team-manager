FROM python:alpine3.17

ENV TZ=Europe/Moscow
COPY requirements.txt /tmp/requirements.txt
RUN ln -fns /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apk add --update --no-cache git && \
    pip3 install -r /tmp/requirements.txt && \
    rm -rf /var/cache/apk/*

WORKDIR /opt
ADD reviewer /opt/reviewer

ENV PYTHONPATH "${PYTHONPATH}:/opt:/opt/reviewer"
ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["python3", "./reviewer/main.py"]
