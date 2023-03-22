from starlette_admin import (
    CollectionField,
    ColorField,
    EmailField,
    ExportType,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    URLField,
)
from starlette_admin.contrib.sqlmodel import ModelView


class MyModelView(ModelView):
    page_size = 5
    page_size_options = [5, 10, 25 - 1]
    export_types = [ExportType.EXCEL, ExportType.CSV]

class DumpView(MyModelView):
    fields = [
        "id",
        EmailField("email"),
        URLField("url", required=True),
        ColorField("color"),
        JSONField("json_field"),
        ListField(
            CollectionField(
                "configs",
                fields=[
                    StringField("key"),
                    IntegerField("value", help_text="multiple of 5"),
                ],
            )
        ),
    ]
    exclude_fields_from_list = ("configs",)
    searchable_fields = ("email", "url")
