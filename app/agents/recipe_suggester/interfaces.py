from abc import ABC, abstractmethod
from typing import List

from app.agents.recipe_suggester.models import Recipe


class RecipeSuggesterAgentABC(ABC):
    @abstractmethod
    async def suggest(self, ingredients: List[str]) -> List[Recipe]:
        pass
