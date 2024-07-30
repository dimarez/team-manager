FROM python:3.11-slim

ENV TZ=Europe/Moscow

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /opt
ADD reviewer /opt/reviewer

ENV PYTHONPATH "${PYTHONPATH}:/opt:/opt/reviewer"
ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["python3", "./reviewer/main.py"]
