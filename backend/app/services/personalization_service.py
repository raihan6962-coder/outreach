import re
from app.models.lead import Lead
from app.models.template import Template
from app.services.template_service import TemplateService


class PersonalizationService:
    @staticmethod
    def prepare_variables(lead: Lead) -> dict:
        first_name = PersonalizationService.extract_first_name(
            lead.developer, lead.email
        )
        return {
            "first_name": first_name,
            "app_name": lead.app_name or "",
            "developer": lead.developer or "",
            "category": lead.category or "",
            "installs": str(lead.installs or ""),
            "keyword": lead.keyword or "",
            "email": lead.email or "",
            "website": lead.website or "",
        }

    @staticmethod
    def render_subject(template: Template, lead: Lead) -> str:
        variables = PersonalizationService.prepare_variables(lead)
        rendered = TemplateService.render_template(template, variables)
        return rendered["subject"]

    @staticmethod
    def render_body(template: Template, lead: Lead) -> str:
        variables = PersonalizationService.prepare_variables(lead)
        rendered = TemplateService.render_template(template, variables)
        return rendered["body_html"]

    @staticmethod
    def extract_first_name(name: str, email: str) -> str:
        if name:
            parts = name.strip().split()
            return parts[0].capitalize()
        if email:
            local_part = email.split("@")[0]
            local_part = re.sub(r"[._\-+]", " ", local_part)
            parts = local_part.split()
            if parts:
                return parts[0].capitalize()
        return "There"
