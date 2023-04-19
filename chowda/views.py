from starlette_admin.contrib.sqla import ModelView
from starlette_admin import BaseField
from dataclasses import dataclass
from json import loads
from requests import Request
from typing import Any, Dict


@dataclass
class MediaFilesGuidLinkField(BaseField):
    render_function_key: str = 'media_file_guid_links'
    display_template = 'displays/media_file_guid_links.html'

    async def serialize_value(self, request: Request, value: Any, action) -> Any:
        return [loads(m.json()) for m in value]

    def dict(self) -> Dict[str, Any]:
        return super().dict()


class CollectionView(ModelView):
    fields: list = [
        'id',
        'name',
        'description',
        MediaFilesGuidLinkField('media_files', label='GUID Links'),
    ]
