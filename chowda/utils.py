from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert


def upsert(
    model: BaseModel,
    value: BaseModel,
    index_elements: list[str],
):
    """Returns the SQLAlchemy statement to upsert a values into a table"""
    return (
        insert(model)
        .values(value.dict())
        .on_conflict_do_update(
            index_elements=index_elements,
            set_=value.dict(),
        )
    )
