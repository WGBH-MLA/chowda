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


def chunks_of_size(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def chunks_striped(lst, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield lst[i::n]


def chunks_sequential(lst, n):
    """Yield n number of sequential chunks from lst."""
    d, r = divmod(len(lst), n)
    for i in range(n):
        si = (d + 1) * (i if i < r else r) + d * (0 if i < r else i - r)
        yield lst[si : si + (d + 1 if i < r else d)]