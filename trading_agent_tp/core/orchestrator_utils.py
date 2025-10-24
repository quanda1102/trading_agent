"""
Utility functions for handling both text-based and structured planner output.

This module provides compatibility between:
1. Old planner (text-based JSON)
2. Enhanced planner (text-based JSON with better prompts)
3. Structured planner (Pydantic models)
"""

import json
from typing import Dict, Any, Union
from .planner_models import Plan, Task


def extract_planner_output(planner_response: Any) -> Dict[str, Any]:
    """
    Extract and normalize planner output.

    Handles three cases:
    1. Pydantic model (from structured planner)
    2. Dict (already parsed)
    3. String (needs JSON parsing)

    Args:
        planner_response: Raw response from planner agent

    Returns:
        Dict with normalized plan data

    Raises:
        ValueError: If output cannot be parsed or validated
    """
    # Extract the content from the response object
    if hasattr(planner_response, 'final_output'):
        content = planner_response.final_output
    elif hasattr(planner_response, 'content'):
        content = planner_response.content
    else:
        content = planner_response

    # Case 1: Pydantic model (structured planner)
    if hasattr(content, 'model_dump'):
        try:
            return content.model_dump()
        except Exception as e:
            raise ValueError(f"Failed to dump Pydantic model: {e}")

    # Case 2: Already a dict
    if isinstance(content, dict):
        return content

    # Case 3: String (needs parsing)
    if isinstance(content, str):
        # Remove markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nContent: {content[:200]}")

    raise ValueError(f"Unknown planner output type: {type(content)}")


def validate_plan_structure(plan_data: Dict[str, Any]) -> bool:
    """
    Validate plan structure.

    Args:
        plan_data: Plan data dict

    Returns:
        True if valid, raises ValueError if invalid
    """
    # Check for final answer
    if plan_data.get("is_final"):
        if "answer" not in plan_data:
            raise ValueError("Final answer missing 'answer' field")
        return True

    # Check for plan
    if "plan" not in plan_data:
        raise ValueError("Missing 'plan' field")

    plan = plan_data["plan"]
    if not isinstance(plan, list):
        raise ValueError(f"Plan must be a list, got {type(plan)}")

    if len(plan) == 0:
        raise ValueError("Plan must contain at least one task")

    # Validate each task
    for i, task in enumerate(plan):
        if not isinstance(task, dict):
            raise ValueError(f"Task {i+1} must be a dict, got {type(task)}")

        required_fields = ["id", "agent", "description"]
        for field in required_fields:
            if field not in task:
                raise ValueError(f"Task {i+1} missing required field: {field}")

        # Validate agent
        valid_agents = ["database", "analysis", "research", "report"]
        if task["agent"] not in valid_agents:
            raise ValueError(f"Task {i+1} has invalid agent: {task['agent']}")

    return True


def normalize_planner_output(planner_response: Any) -> Dict[str, Any]:
    """
    Extract and validate planner output in one step.

    Args:
        planner_response: Raw response from planner

    Returns:
        Normalized and validated plan data

    Raises:
        ValueError: If extraction or validation fails
    """
    # Extract
    plan_data = extract_planner_output(planner_response)

    # Validate
    validate_plan_structure(plan_data)

    # Add defaults
    if "is_final" not in plan_data:
        plan_data["is_final"] = False

    if not plan_data["is_final"]:
        if "estimated_cycles" not in plan_data:
            plan_data["estimated_cycles"] = 2

        # Add defaults to tasks
        for task in plan_data["plan"]:
            if "loop_back" not in task:
                task["loop_back"] = True
            if "depends_on" not in task:
                task["depends_on"] = None
            if "required_confidence" not in task:
                task["required_confidence"] = 0.7

    return plan_data


def validate_with_pydantic(plan_data: Dict[str, Any]) -> Plan:
    """
    Validate plan data with Pydantic model.

    Args:
        plan_data: Plan data dict

    Returns:
        Validated Plan object

    Raises:
        ValidationError: If data doesn't match schema
    """
    return Plan.model_validate(plan_data)


# Example usage
if __name__ == "__main__":
    # Test with various input formats

    # Format 1: Dict (already parsed)
    test_dict = {
        "plan": [
            {
                "id": 1,
                "agent": "database",
                "description": "Get BTC data",
                "loop_back": True,
                "depends_on": None,
                "required_confidence": 0.9
            }
        ],
        "estimated_cycles": 2
    }

    result = normalize_planner_output(test_dict)
    print("✅ Dict input:", result)

    # Format 2: JSON string
    test_json = '''
    {
        "plan": [
            {
                "id": 1,
                "agent": "database",
                "description": "Get BTC data",
                "loop_back": true,
                "depends_on": null,
                "required_confidence": 0.9
            }
        ],
        "estimated_cycles": 2
    }
    '''

    result = normalize_planner_output(test_json)
    print("✅ JSON string input:", result)

    # Format 3: JSON with markdown
    test_markdown = '''```json
    {
        "plan": [
            {
                "id": 1,
                "agent": "database",
                "description": "Get BTC data",
                "loop_back": true,
                "depends_on": null,
                "required_confidence": 0.9
            }
        ],
        "estimated_cycles": 2
    }
    ```'''

    result = normalize_planner_output(test_markdown)
    print("✅ Markdown JSON input:", result)

    # Validate with Pydantic
    plan_obj = validate_with_pydantic(result)
    print("✅ Pydantic validation passed:", plan_obj.model_dump())

    print("\n🎉 All formats handled successfully!")