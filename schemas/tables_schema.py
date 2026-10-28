from pydantic import BaseModel, ConfigDict, Field

class TableBase(BaseModel):
    id: int
    user_id: int
    table_number: int
    capacity: int
    is_reserved: bool
    reserved_date: str

class TableResponse(TableBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    table_number: int
    capacity: int
    is_reserved: bool
    reserved_date: str

class TableCreate(BaseModel):
    user_id: int
    table_number: int
    capacity: int
    is_reserved: bool
    reserved_date: str

class TableUpdate(BaseModel):
    is_reserved: bool
    reserved_date: str