from typing import List

from pydantic import BaseModel


class Recipe(BaseModel):
    name: str
    description: str
    ingredients: List[str]
    category: str
    steps: List[str]


class RecipeSuggesterAgentDependencies(BaseModel):
    ingredients: List[str]
