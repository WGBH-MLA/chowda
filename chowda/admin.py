from starlette_admin.contrib.sqlmodel import Admin as BaseAdmin
from requests import Request
from typing import Optional


class Admin(BaseAdmin):
    """Custom Admin class"""

    def custom_render_js(self, request: Request) -> Optional[str]:
        return request.url_for('static', path='js/custom_render.js')