from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from loguru import logger as log


def render_template(template_filename: str, context: dict) -> str | None:
    try:
        env = Environment(loader=FileSystemLoader('templates'), autoescape=False)
        template = env.get_template(template_filename)
        output_from_parsed_template = template.render(context)
        return output_from_parsed_template
    except TemplateNotFound:
        log.error(f"Не найден шаблон [{template_filename}]")
        return None



