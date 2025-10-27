"""
Pydantic models for Planner Agent structured output.

These models ensure the planner always outputs valid, parseable JSON.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single task in the execution plan."""

    id: int = Field(
        ...,
        description="Unique task ID (1, 2, 3, ...)",
        ge=1
    )

    agent: Literal["database", "analysis", "research", "report"] = Field(
        ...,
        description="Which agent should execute this task"
    )

    description: str = Field(
        ...,
        description="Clear, actionable task description",
        max_length=500
    )

    loop_back: bool = Field(
        ...,
        description="Whether results should loop back to planner (false only for final report tasks)"
    )

    depends_on: Optional[List[int]] = Field(
        None,
        description="List of task IDs that must complete before this task, or null for no dependencies"
    )

    required_confidence: float = Field(
        0.7,
        description="Minimum confidence threshold (0.0-1.0)",
        ge=0.0,
        le=1.0
    )


class Plan(BaseModel):
    """Complete execution plan with tasks and metadata."""

    plan: List[Task] = Field(
        ...,
        description="List of tasks to execute",
        min_length=1,
        max_length=10
    )

    estimated_cycles: int = Field(
        2,
        description="Estimated number of planning-execution cycles needed (1-5)",
        ge=1,
        le=5
    )


class FinalAnswer(BaseModel):
    """Final answer when no further planning is needed."""

    is_final: bool = Field(
        True,
        description="Indicates this is a final answer, not a plan"
    )

    answer: str = Field(
        ...,
        description="The final answer to the user's question"
    )


# Example usage for agent configuration
PLAN_EXAMPLE = {
    "plan": [
        {
            "id": 1,
            "agent": "database",
            "description": "Retrieve BTC data from crypto_kline_hours (1h interval) for last 168 hours",
            "loop_back": True,
            "depends_on": None,
            "required_confidence": 0.9
        },
        {
            "id": 2,
            "agent": "research",
            "description": "Search for BTC news from last 24-48 hours only",
            "loop_back": True,
            "depends_on": None,
            "required_confidence": 0.6
        },
        {
            "id": 3,
            "agent": "analysis",
            "description": "Calculate SHORT-TERM indicators: RSI(14), MACD(12,26,9), EMA(20,50)",
            "loop_back": True,
            "depends_on": [1],
            "required_confidence": 0.8
        },
        {
            "id": 4,
            "agent": "report",
            "description": "Generate SHORT-TERM Vietnamese report with 4H analysis",
            "loop_back": False,
            "depends_on": [1, 2, 3],
            "required_confidence": 0.9
        }
    ],
    "estimated_cycles": 2
}
