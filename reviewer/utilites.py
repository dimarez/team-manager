import os
import sys

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from loguru import logger as log


def render_template(template_filename: str, context: dict) -> str | None:
    try:
        templates_dir = os.path.join(os.path.abspath(sys.path[0]), "templates")
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

        template = env.get_template(template_filename)
        output_from_parsed_template = template.render(context)
        return output_from_parsed_template
    except TemplateNotFound:
        log.error(f"Не найден шаблон [{template_filename}]")
        return None
