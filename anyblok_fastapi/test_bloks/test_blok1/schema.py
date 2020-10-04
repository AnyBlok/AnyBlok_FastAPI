from pydantic import BaseModel


class ExampleCreateSchema(BaseModel):
    name: str


class ExampleSchema(ExampleCreateSchema):
    id: int
    name: str

    class Config:
        orm_mode = True
