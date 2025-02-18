from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.recipe_suggester.agent import RecipeSuggesterAgent
from app.agents.recipe_suggester.interfaces import RecipeSuggesterAgentABC
from app.agents.recipe_suggester.models import Recipe
from loguru import logger

router = APIRouter()


class RecipeSuggestBody(BaseModel):
    ingredients: List[str]


@router.post("/recipes/suggest", response_model=List[Recipe])
async def recipe_suggest(body: RecipeSuggestBody):
    logger.info(f"Request received with ingredients: {body.ingredients}")
    ingredients = body.ingredients
    agent: RecipeSuggesterAgentABC = RecipeSuggesterAgent()
    recipes = await agent.suggest(ingredients)
    logger.info(f"Recipes suggested: {recipes}")

    return recipes
