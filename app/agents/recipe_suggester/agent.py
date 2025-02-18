from typing import List

from pydantic_ai import Agent, RunContext
from app.agents.recipe_suggester.interfaces import RecipeSuggesterAgentABC
from app.agents.recipe_suggester.models import (
    Recipe,
    RecipeSuggesterAgentDependencies,
)


class RecipeSuggesterAgent(RecipeSuggesterAgentABC):
    def __init__(self):
        self.agent = Agent(
            "openai:gpt-4o-mini",
            deps_type=RecipeSuggesterAgentDependencies,
            result_type=List[Recipe],
            system_prompt=(
                """
                    You are a helpful Recipe Suggester AI.
                    Given a list of ingredients provided by the user, you will suggest two recipes that can be made using those ingredients.
                """
            ),
        )

        @self.agent.system_prompt
        async def add_ingredients(
            ctx: RunContext[RecipeSuggesterAgentDependencies],
        ) -> str:
            ingredients = ctx.deps.ingredients

            return f"The ingredients are {', '.join(ingredients)}"

    async def suggest(self, ingredients: List[str]) -> List[Recipe]:
        result = await self.agent.run(
            "Suggest a recipe",
            deps=RecipeSuggesterAgentDependencies(ingredients=ingredients),
        )

        return result.data
