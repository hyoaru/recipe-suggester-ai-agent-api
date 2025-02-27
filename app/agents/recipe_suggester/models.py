from typing import List

from pydantic import BaseModel


class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    steps: List[str]


class RecipeSuggesterAgentDependencies(BaseModel):
    ingredients: List[str]
