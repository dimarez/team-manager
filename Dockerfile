# syntax=docker/dockerfile:1
from python:slim

RUN pip install python-gitlab pyyaml pytest pydantic loguru