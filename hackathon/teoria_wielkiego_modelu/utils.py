from typing import Any, Dict, Optional

from langchain.schema import BaseMessage


def add_role(message: BaseMessage, role: Optional[str] = None) -> BaseMessage:
    if role is not None:
        message.name = role
    return message


def message_to_dict(message: BaseMessage) -> Dict[str, Any]:
    result = {
        "role": message.name or message.type,
        "content": message.content,
        "additional_kwargs": message.additional_kwargs,
    }

    # Only add these fields if they exist
    if hasattr(message, "usage_metadata"):
        result["usage_metadata"] = message.usage_metadata
    if hasattr(message, "response_metadata"):
        result["response_metadata"] = message.response_metadata

    return result


def calculate_message_cost(message: Dict[str, Any]) -> float:
    """Calculate the cost of a message based on its metadata.

    Args:
        message: A dictionary containing message data with usage_metadata and response_metadata

    Returns:
        float: The calculated cost in USD
    """
    # Default costs per 1K tokens (as of 2024)
    COSTS = {
        "gpt-4o-mini": {
            "input": 0.00015,
            "output": 0.0006,
        },
        "gpt-4o": {
            "input": 0.0025,
            "output": 0.01,
        },
        "o3-mini": {
            "input": 0.0011,
            "output": 0.0022,
        },
    }

    # Get model name from response metadata
    model_name = (
        message.get("response_metadata", {}).get("model_name", "").split("-20")[0]
    )

    # Get token counts from usage metadata
    usage = message.get("usage_metadata", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Get costs for the model
    model_costs = COSTS.get(model_name, {"input": 0.0, "output": 0.0})

    # Calculate input and output costs separately
    input_cost = (input_tokens / 1000) * model_costs["input"]
    output_cost = (output_tokens / 1000) * model_costs["output"]

    # Calculate total cost
    total_cost = input_cost + output_cost

    return round(total_cost, 4)
