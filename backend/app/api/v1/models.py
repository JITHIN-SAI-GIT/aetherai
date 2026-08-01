from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

class ModelObj(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "system"

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelObj]

router = APIRouter(tags=["Models"])

@router.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(
        data=[
            ModelObj(id="gpt-4-turbo"),
            ModelObj(id="gpt-3.5-turbo"),
            ModelObj(id="claude-3-opus"),
            ModelObj(id="gemini-pro"),
        ]
    )

@router.get("/v1/models/{model}", response_model=ModelObj)
async def get_model(model: str):
    return ModelObj(id=model)
