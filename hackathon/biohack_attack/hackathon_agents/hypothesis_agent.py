from agents import Agent

from biohack_attack.model_factory import ModelFactory, ModelType

hypothesis = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
        model=ModelFactory.build_model(ModelType.GEMINI),
        tools=[],
)