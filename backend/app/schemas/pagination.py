from pydantic import BaseModel


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int


class PaginatedResponse[T](BaseModel):
    items: list[T]
    pagination: PaginationMeta
