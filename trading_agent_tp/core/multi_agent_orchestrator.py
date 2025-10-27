"""
Multi-Agent Orchestrator

Coordinates specialized agents (Database, Analysis, Research, Report) with
intelligent task delegation and result aggregation.
"""

import json
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
from agents import Runner

# Use structured planner (Pydantic - zero JSON errors)
from .planner_agent_structured import planner_agent_structured as planner_agent
print("✅ Using structured planner with Pydantic (zero JSON errors)")

from ..agents import database_agent, analysis_agent, research_agent, report_agent


class MultiAgentOrchestrationError(Exception):
    """Custom exception for multi-agent orchestration errors."""
    pass


class MultiAgentOrchestrator:
    """Orchestrates specialized agents for trading analysis."""

    DEFAULT_MAX_CYCLES = 3  # Default maximum planning-execution cycles

    def __init__(self):
        """Initialize orchestrator with agents and runner."""
        self.runner = Runner()
        self.shared_history: List[Dict[str, Any]] = []
        self.trace_events: List[Dict[str, Any]] = []
        self.max_cycles = self.DEFAULT_MAX_CYCLES  # Will be updated based on planner estimate
        self.hard_cycle_limit = 8  # Prevent infinite loops while allowing flexibility
        self.completed_task_ids: Set[int] = set()
        self.completed_task_signatures: Set[str] = set()

        # Agent registry for task delegation
        self.agents = {
            "database": database_agent,
            "analysis": analysis_agent,
            "research": research_agent,
            "report": report_agent
        }

    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        memory_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query through specialized agents.

        Args:
            query: User's question
            user_id: User identifier
            session_id: Session identifier
            memory_context: Previous conversation context

        Returns:
            Dict with keys:
                - final_answer: str
                - plan_history: List[Dict]
                - execution_log: List[Dict]
                - agent_results: Dict[str, Any]
                - cycles_used: int
                - success: bool
                - error: Optional[str]
        """
        # Initialize
        self.shared_history = []
        self.trace_events = []
        plan_history = []
        execution_log = []
        self.max_cycles = self.DEFAULT_MAX_CYCLES
        self.completed_task_ids = set()
        self.completed_task_signatures = set()
        agent_results = {
            "database": None,
            "analysis": None,
            "research": None,
            "report": None
        }

        try:
            # Prepare initial query with memory context
            initial_query = self._prepare_initial_query(query, memory_context)

            self.shared_history.append({
                "role": "user",
                "content": initial_query
            })

            # Planning-execution loop
            cycle = 0
            while cycle < self.max_cycles:
                cycle_number = cycle + 1
                print(f"\n{'='*80}")
                print(f"CYCLE {cycle_number}/{self.max_cycles}")
                print(f"{'='*80}")

                # PHASE 1: PLANNING
                plan_started_at = self._utcnow()
                try:
                    plan_result = await self._planning_phase(cycle_number)
                    plan_completed_at = self._utcnow()
                    planner_message = plan_result.get("planner_message", "")

                    # Check for final answer
                    if plan_result["is_final"]:
                        self._append_event(
                            event_type="final",
                            cycle=cycle_number,
                            agent="planner",
                            status="success",
                            content=plan_result["final_answer"],
                            started_at=plan_started_at,
                            completed_at=plan_completed_at,
                            metadata={"planner_message": planner_message}
                        )

                        return self._build_success_response(
                            final_answer=plan_result["final_answer"],
                            plan_history=plan_history,
                            execution_log=execution_log,
                            agent_results=agent_results,
                            cycles_used=cycle_number
                        )

                    # Add plan to history
                    plan_history.append({
                        "cycle": cycle_number,
                        "plan": plan_result["plan"],
                        "planner_message": planner_message,
                        "created_at": plan_completed_at.isoformat()
                    })

                    self._append_event(
                        event_type="plan",
                        cycle=cycle_number,
                        agent="planner",
                        status="success",
                        content=planner_message,
                        started_at=plan_started_at,
                        completed_at=plan_completed_at,
                        metadata={"tasks": plan_result["plan"]}
                    )

                    print(f"\n📋 Plan Created: {len(plan_result['plan'])} tasks")

                except Exception as e:
                    plan_completed_at = self._utcnow()
                    error_msg = f"❌ Planning failed in cycle {cycle_number}: {str(e)}"
                    print(error_msg)

                    self._append_event(
                        event_type="plan",
                        cycle=cycle_number,
                        agent="planner",
                        status="failed",
                        content=str(e),
                        started_at=plan_started_at,
                        completed_at=plan_completed_at,
                        metadata={"error": str(e)}
                    )

                    return self._build_error_response(
                        error_msg=error_msg,
                        plan_history=plan_history,
                        execution_log=execution_log,
                        agent_results=agent_results,
                        cycles_used=cycle_number
                    )

                # PHASE 2: EXECUTION WITH PARALLEL DELEGATION
                # Execute tasks with dependency resolution and parallel execution
                final_result, cycle_stats = await self._execute_tasks_with_dependencies(
                    tasks=plan_result["plan"],
                    cycle=cycle_number,
                    agent_results=agent_results,
                    execution_log=execution_log
                )

                # Check if a task with loop_back=false was executed and returned
                if final_result is not None:
                    return final_result

                self._extend_cycles_if_needed(cycle_number, cycle_stats)

                cycle += 1

                # PHASE 3: LOOP BACK TO PLANNER
                # All tasks with loop_back=true will loop back to planner for next cycle
                # Tasks with loop_back=false have already returned above (line 229-254)
                # Planner will analyze results and decide:
                #   - Output "FINAL ANSWER:" if complete
                #   - Create new plan with report task (agent="report", loop_back=false) if ready
                #   - Create new data-gathering tasks if more clarification needed

            # Max cycles reached
            print(f"\n⚠️ Maximum cycles ({self.max_cycles}) reached")
            timeout_timestamp = self._utcnow()
            self._append_event(
                event_type="error",
                cycle=self.max_cycles,
                agent="planner",
                status="timeout",
                content="Maximum planning cycles reached",
                started_at=timeout_timestamp,
                completed_at=timeout_timestamp,
                metadata={}
            )

            return self._build_timeout_response(
                plan_history=plan_history,
                execution_log=execution_log,
                agent_results=agent_results
            )

        except Exception as e:
            error_msg = f"❌ Orchestration error: {str(e)}"
            print(error_msg)
            error_timestamp = self._utcnow()
            self._append_event(
                event_type="error",
                cycle=0,
                agent="orchestrator",
                status="failed",
                content=str(e),
                started_at=error_timestamp,
                completed_at=error_timestamp,
                metadata={}
            )
            return self._build_error_response(
                error_msg=error_msg,
                plan_history=plan_history,
                execution_log=execution_log,
                agent_results=agent_results,
                cycles_used=0
            )

    def _has_sufficient_data(self, agent_results: Dict[str, Any]) -> bool:
        """
        Check if we have sufficient data from agents to generate final report.

        Criteria:
        - Must have data from at least DatabaseAgent OR AnalysisAgent
        - Optional: ResearchAgent (for news/sentiment)
        - Must NOT already have ReportAgent result

        Returns:
            True if ready to generate report, False otherwise
        """
        # Don't generate report if already done
        if agent_results.get("report") is not None:
            return False

        # Check if we have core data (database or analysis)
        has_database = agent_results.get("database") is not None
        has_analysis = agent_results.get("analysis") is not None

        # Must have at least one of: database or analysis
        return has_database or has_analysis

    def _identify_agent_for_task(self, task_description: str) -> str:
        """
        Identify which specialized agent should handle the task.

        Returns:
            Agent type: "database", "analysis", "research", or "report"
        """
        task_lower = task_description.lower()

        # Keywords for each agent type
        database_keywords = [
            "retrieve", "fetch", "get data", "database", "query",
            "ohlcv", "price data", "volume data", "historical"
        ]

        analysis_keywords = [
            "calculate", "analyze", "indicator", "rsi", "macd",
            "moving average", "bollinger", "support", "resistance",
            "pattern", "technical", "ema", "atr", "pivot"
        ]

        research_keywords = [
            "search", "news", "sentiment", "web", "fact check",
            "verify", "market research", "google", "latest updates"
        ]

        report_keywords = [
            "format", "report", "generate", "structure", "output",
            "vietnamese", "tiếng việt", "summarize", "present"
        ]

        # Score each agent
        scores = {
            "database": sum(1 for kw in database_keywords if kw in task_lower),
            "analysis": sum(1 for kw in analysis_keywords if kw in task_lower),
            "research": sum(1 for kw in research_keywords if kw in task_lower),
            "report": sum(1 for kw in report_keywords if kw in task_lower)
        }

        # Return agent with highest score
        agent_type = max(scores, key=scores.get)

        # If no clear match, default to analysis for technical tasks
        if scores[agent_type] == 0:
            agent_type = "analysis"

        return agent_type

    async def _execute_with_agent(
        self,
        agent_type: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task with specified specialized agent.

        Returns:
            Dict with keys: result
        """
        agent = self.agents[agent_type]
        task_id = task["id"]
        task_desc = task["description"]

        # Prepare agent input with context
        agent_input = self._format_task_for_agent(task, agent_type)

        # Run agent
        agent_response = await self.runner.run(agent, agent_input)

        agent_content = self._extract_content(agent_response)

        # Add to shared history
        task_result = f"Task {task_id} ({agent_type}Agent): {agent_content}"
        self.shared_history.append({
            "role": "assistant",
            "content": task_result,
            "agent": agent_type
        })

        return {
            "result": agent_content
        }

    async def _planning_phase(self, cycle_num: int) -> Dict[str, Any]:
        """
        Execute planning phase.

        Returns:
            Dict with keys: is_final, final_answer (if final), plan (if not final)
        """
        last_error: Optional[Exception] = None

        for attempt in range(3):
            planner_input = self._format_history_for_planner()

            # Run planner
            planner_response = await self.runner.run(planner_agent, planner_input)
            planner_content = self._extract_content(planner_response)

            # Add to shared history
            self.shared_history.append({
                "role": "assistant",
                "content": planner_content,
                "agent": "planner"
            })

            content_cleaned = planner_content.strip()

            # Remove markdown code fences if present
            if content_cleaned.startswith("```"):
                content_cleaned = re.sub(r'^```(?:json|markdown)?\\s*', '', content_cleaned)
                content_cleaned = re.sub(r'\\s*```$', '', content_cleaned)
                content_cleaned = content_cleaned.strip()

            parsed_json: Optional[Dict[str, Any]] = None
            try:
                parsed_candidate = json.loads(content_cleaned)
                if isinstance(parsed_candidate, dict):
                    parsed_json = parsed_candidate
            except json.JSONDecodeError:
                parsed_json = None

            if parsed_json and parsed_json.get("is_final") is True:
                final_answer = parsed_json.get("answer") or parsed_json.get("final_answer", "")
                return {
                    "is_final": True,
                    "final_answer": final_answer,
                    "planner_message": planner_content
                }

            if "FINAL ANSWER:" in content_cleaned.upper():
                final_marker_match = re.search(r'FINAL\\s+ANSWER\\s*:', content_cleaned, re.IGNORECASE)
                if final_marker_match:
                    final_answer = content_cleaned[final_marker_match.end():].strip()
                    return {
                        "is_final": True,
                        "final_answer": final_answer,
                        "planner_message": planner_content
                    }

            try:
                plan_data = parsed_json if parsed_json and "plan" in parsed_json else self._parse_plan(planner_content)
            except MultiAgentOrchestrationError as e:
                last_error = e
                warning = (
                    "⚠️ Planner output không hợp lệ. Vui lòng trả về JSON đúng chuẩn 'plan' "
                    "hoặc 'FINAL ANSWER'."
                )
                self.shared_history.append({
                    "role": "assistant",
                    "agent": "orchestrator",
                    "status": "failed",
                    "content": warning
                })
                continue

            if isinstance(plan_data, dict) and "plan" in plan_data:
                plan = plan_data["plan"]
                estimated_cycles = plan_data.get("estimated_cycles")
                if estimated_cycles and cycle_num == 1:
                    self.max_cycles = min(max(estimated_cycles, 1), 5)
                    print(f"⚙️  Dynamic cycles: Planner estimated {estimated_cycles} cycles, using max_cycles={self.max_cycles}")
            else:
                plan = plan_data if isinstance(plan_data, list) else plan_data.get("plan", [])

            return {
                "is_final": False,
                "plan": plan,
                "planner_message": planner_content
            }

        raise last_error or MultiAgentOrchestrationError(
            "Planner failed to return a valid plan after multiple attempts"
        )

    def _format_task_for_agent(
        self,
        task: Dict[str, Any],
        agent_type: str
    ) -> str:
        """Format task for specific agent with relevant context."""
        task_desc = f"Task {task['id']}: {task['description']}"

        # Special handling for ReportAgent - needs all previous results
        if agent_type == "report":
            context_parts = [task_desc, "\n## AGGREGATED RESULTS FROM AGENTS\n"]

            # Collect results from all agents
            for msg in self.shared_history:
                if msg.get("role") == "assistant" and msg.get("agent") in ["database", "analysis", "research"]:
                    agent_name = msg.get("agent", "").capitalize()
                    # Extract just the result part (remove "Task X (...Agent):" prefix)
                    content = msg.get("content", "")
                    if "Agent):" in content:
                        content = content.split("Agent):", 1)[1].strip()
                    context_parts.append(f"\n### {agent_name}Agent Results:\n{content}\n")

            return "\n".join(context_parts)

        # For other agents, include limited context
        context_parts = [task_desc]

        for msg in self.shared_history:
            if msg.get("role") == "assistant" and msg.get("agent") in self.agents:
                # Include results from other agents for context
                agent_name = msg.get("agent", "").capitalize()
                content = msg.get("content", "")
                if "Agent):" in content:
                    content = content.split("Agent):", 1)[1].strip()
                context_parts.append(f"\nPrevious {agent_name}Agent result: {content[:300]}...")

        return "\n".join(context_parts[-5:])  # Last 5 context items

    def _prepare_initial_query(self, query: str, memory_context: Optional[str]) -> str:
        """Prepare initial query with memory context."""
        if memory_context:
            return f"Previous conversation:\n{memory_context}\n\nCurrent question: {query}"
        return query

    def _format_history_for_planner(self) -> str:
        """Format shared history for planner input."""
        messages = []

        for msg in self.shared_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            agent = msg.get("agent", "")
            status = msg.get("status", "")

            if role == "user":
                messages.append(f"User: {content}")
            elif role == "assistant":
                status_marker = " [FAILED]" if status == "failed" else ""
                if agent == "planner":
                    messages.append(f"Planner{status_marker}: {content}")
                elif agent in self.agents:
                    messages.append(f"{agent.capitalize()}Agent{status_marker}: {content}")
                else:
                    messages.append(f"Assistant{status_marker}: {content}")

        return "\n\n".join(messages)

    async def _execute_tasks_with_dependencies(
        self,
        tasks: List[Dict[str, Any]],
        cycle: int,
        agent_results: Dict[str, Any],
        execution_log: List[Dict]
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, int]]:
        """
        Execute tasks with dependency resolution and parallel execution.

        Args:
            tasks: List of tasks to execute
            cycle: Current cycle number
            agent_results: Accumulated agent results
            execution_log: Execution log to append to

        Returns:
            Tuple[Optional[Dict[str, Any]], Dict[str, int]] where the first element is
            the final response (if a task with loop_back=false completed) and the second
            element summarises cycle statistics (succeeded/failed/skipped/pending).
        """
        completed_tasks: Set[int] = set()
        task_results: Dict[int, Dict[str, Any]] = {}
        succeeded = 0
        failed = 0
        skipped = 0

        # Build dependency graph
        remaining_tasks: Dict[int, Dict[str, Any]] = {}
        for task in tasks:
            if self._is_task_already_completed(task):
                skipped += 1
                completed_tasks.add(task["id"])
                self.completed_task_ids.add(task["id"])
                print(f"🔁 Skipping completed task {task['id']}: {task['description'][:80]}")
            else:
                remaining_tasks[task["id"]] = task

        # Ensure default dependencies when planner omitted them
        def _normalise_dependencies(task: Dict[str, Any]) -> List[int]:
            deps = task.get("depends_on")
            if deps is None:
                return []
            if isinstance(deps, list):
                return [int(dep) for dep in deps]
            return [int(dep) for dep in [deps]]

        # Auto-inject dependencies based on agent chain (report waits for others, analysis waits for data)
        if any(task.get("agent") == "report" for task in tasks):
            data_task_ids = [
                t["id"] for t in tasks
                if t.get("agent") in {"database", "analysis", "research"}
            ]
            for task in tasks:
                if task.get("agent") == "report":
                    task.setdefault("depends_on", [])
                    current_deps = set(_normalise_dependencies(task))
                    for dep_id in data_task_ids:
                        current_deps.add(dep_id)
                    task["depends_on"] = sorted(current_deps)

        if any(task.get("agent") == "analysis" for task in tasks):
            database_task_ids = [
                t["id"] for t in tasks if t.get("agent") == "database"
            ]
            if database_task_ids:
                for task in tasks:
                    if task.get("agent") == "analysis":
                        task.setdefault("depends_on", [])
                        current_deps = set(_normalise_dependencies(task))
                        for dep_id in database_task_ids:
                            if dep_id != task["id"]:
                                current_deps.add(dep_id)
                        task["depends_on"] = sorted(current_deps)

        remaining_tasks = {task["id"]: task for task in tasks}

        while remaining_tasks:
            # Find tasks that can run now (all dependencies satisfied)
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                depends_on = task.get("depends_on") or []
                if all(
                    dep_id in completed_tasks or dep_id in self.completed_task_ids
                    for dep_id in depends_on
                ):
                    ready_tasks.append(task)

            if not ready_tasks:
                # Circular dependency or impossible to complete
                print(f"⚠️  No ready tasks found. Remaining: {list(remaining_tasks.keys())}")
                break

            # Execute ready tasks in parallel
            print(f"\n🚀 Executing {len(ready_tasks)} task(s) in parallel")

            parallel_results = await asyncio.gather(
                *[self._execute_single_task(task, cycle, agent_results, execution_log)
                  for task in ready_tasks],
                return_exceptions=True
            )

            # Process results
            for task, result in zip(ready_tasks, parallel_results):
                task_id = task["id"]

                if isinstance(result, Exception):
                    print(f"❌ Task {task_id} failed with exception: {str(result)}")
                    # Mark as completed even if failed so we don't block dependent tasks
                    completed_tasks.add(task_id)
                    self.completed_task_ids.add(task_id)
                    failed += 1
                    remaining_tasks.pop(task_id, None)
                    continue

                if result is not None and result.get("is_final"):
                    completed_tasks.add(task_id)
                    self.completed_task_ids.add(task_id)
                    self.completed_task_signatures.add(self._task_signature(task))
                    remaining_tasks.pop(task_id, None)
                    succeeded += 1
                    cycle_stats = {
                        "succeeded": succeeded,
                        "failed": failed,
                        "skipped": skipped,
                        "pending": len(remaining_tasks)
                    }
                    return result["response"], cycle_stats

                completed_tasks.add(task_id)
                self.completed_task_ids.add(task_id)
                self.completed_task_signatures.add(self._task_signature(task))
                task_results[task_id] = result
                remaining_tasks.pop(task_id, None)
                succeeded += 1

        cycle_stats = {
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "pending": len(remaining_tasks)
        }

        return None, cycle_stats

    def _task_signature(self, task: Dict[str, Any]) -> str:
        agent = task.get("agent")
        description = task.get("description", "")
        if not agent:
            agent = self._identify_agent_for_task(description)
        agent = (agent or "unknown").strip().lower()
        return f"{agent}::{description.strip().lower()}"

    def _is_task_already_completed(self, task: Dict[str, Any]) -> bool:
        return self._task_signature(task) in self.completed_task_signatures

    def _extend_cycles_if_needed(self, cycle_number: int, cycle_stats: Dict[str, int]) -> None:
        if (
            cycle_number >= self.max_cycles
            and self.max_cycles < self.hard_cycle_limit
            and (cycle_stats.get("failed", 0) > 0 or cycle_stats.get("pending", 0) > 0)
        ):
            self.max_cycles += 1
            print(f"🔁 Extending max_cycles to {self.max_cycles} to retry incomplete tasks")

    async def _execute_single_task(
        self,
        task: Dict[str, Any],
        cycle: int,
        agent_results: Dict[str, Any],
        execution_log: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a single task.

        Returns:
            Dict with is_final=True and response if loop_back=false, otherwise result dict
        """
        task_id = task["id"]
        task_desc = task["description"]
        agent_type = task.get("agent") or self._identify_agent_for_task(task_desc)
        loop_back = task.get("loop_back", True)
        required_confidence = task.get("required_confidence", 0.7)

        print(f"\n🔧 Executing Task {task_id}: {task_desc[:80]}...")
        print(f"   → Agent: {agent_type.upper()}Agent | Loop back: {loop_back} | Required confidence: {required_confidence}")

        task_started_at = self._utcnow()
        try:
            exec_result = await self._execute_with_agent(
                agent_type=agent_type,
                task=task
            )

            task_completed_at = self._utcnow()
            duration_ms = self._duration_ms(task_started_at, task_completed_at)

            # Store agent result
            if agent_results[agent_type] is None:
                agent_results[agent_type] = []
            agent_results[agent_type].append({
                "task_id": task_id,
                "result": exec_result["result"]
            })

            self.completed_task_signatures.add(self._task_signature(task))

            execution_log.append({
                "cycle": cycle,
                "task_id": task_id,
                "task": task_desc,
                "agent": agent_type,
                "result": exec_result["result"],
                "success": True,
                "started_at": task_started_at.isoformat(),
                "completed_at": task_completed_at.isoformat(),
                "duration_ms": duration_ms,
                "required_confidence": required_confidence
            })

            self._append_event(
                event_type="action",
                cycle=cycle,
                agent=agent_type,
                status="success",
                content=exec_result["result"],
                started_at=task_started_at,
                completed_at=task_completed_at,
                metadata={
                    "task_id": task_id,
                    "description": task_desc,
                    "required_confidence": required_confidence
                }
            )

            print(f"✅ Task {task_id} completed by {agent_type.upper()}Agent ({duration_ms}ms)")
            result_preview = exec_result['result'][:150]
            print(f"   Preview: {result_preview}...")

            # Check if this task should NOT loop back (final task)
            if not loop_back:
                print(f"\n🎯 Task {task_id} marked as FINAL (loop_back=false)")
                print(f"   → Returning immediately without further planning")

                self._append_event(
                    event_type="final",
                    cycle=cycle,
                    agent=agent_type,
                    status="success",
                    content=exec_result["result"],
                    started_at=task_started_at,
                    completed_at=task_completed_at,
                    metadata={
                        "task_id": task_id,
                        "description": task_desc,
                        "loop_back": False
                    }
                )

                return {
                    "is_final": True,
                    "response": self._build_success_response(
                        final_answer=exec_result["result"],
                        plan_history=[],
                        execution_log=execution_log,
                        agent_results=agent_results,
                        cycles_used=cycle
                    )
                }

            return {"result": exec_result}

        except Exception as e:
            error_result = f"❌ Task execution failed: {str(e)}"

            task_completed_at = self._utcnow()
            duration_ms = self._duration_ms(task_started_at, task_completed_at)

            execution_log.append({
                "cycle": cycle,
                "task_id": task_id,
                "task": task_desc,
                "agent": agent_type,
                "result": error_result,
                "success": False,
                "started_at": task_started_at.isoformat(),
                "completed_at": task_completed_at.isoformat(),
                "duration_ms": duration_ms,
                "required_confidence": required_confidence
            })

            print(f"❌ Task {task_id} failed: {str(e)}")

            self._append_event(
                event_type="action",
                cycle=cycle,
                agent=agent_type,
                status="failed",
                content=str(e),
                started_at=task_started_at,
                completed_at=task_completed_at,
                metadata={
                    "task_id": task_id,
                    "description": task_desc
                }
            )

            # Add failure to shared history so planner can adapt
            self.shared_history.append({
                "role": "assistant",
                "content": f"Task {task_id} result: {error_result}",
                "agent": "executor",
                "status": "failed"
            })

            raise e

    def _parse_plan(self, planner_content: str) -> Dict[str, Any]:
        """
        Parse JSON plan from planner response.

        Handles:
        - Pydantic models (from structured planner)
        - Dict (already parsed)
        - JSON strings (with repair attempts)

        Returns:
            Dict with 'plan' and 'estimated_cycles' keys

        Raises:
            MultiAgentOrchestrationError: If plan cannot be parsed
        """
        try:
            # Check if it's already a Pydantic model
            if hasattr(planner_content, 'model_dump'):
                # It's a Pydantic model - convert to dict
                return planner_content.model_dump()

            # Check if it's already a dict
            if isinstance(planner_content, dict):
                # Validate structure
                if "plan" in planner_content:
                    return planner_content
                else:
                    raise MultiAgentOrchestrationError(
                        f"❌ Plan dict missing 'plan' key. Keys: {list(planner_content.keys())}"
                    )

            # It's a string - parse as JSON
            content = str(planner_content).strip()

            # Remove markdown code fences
            content = re.sub(r'^```json?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()

            # Try to find JSON object - handle both complete and incomplete JSON
            json_match = re.search(r'\{.*?"plan"\s*:\s*\[.*?\].*?\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

            # If JSON seems incomplete, try to complete it
            if content.count('{') > content.count('}'):
                # Add missing closing braces
                content += '}' * (content.count('{') - content.count('}'))

            if content.count('[') > content.count(']'):
                # Add missing closing brackets
                content += ']' * (content.count('[') - content.count(']'))

            # Parse JSON
            try:
                plan_data = json.loads(content)
                if isinstance(plan_data, list):
                    plan_data = {"plan": plan_data}
                elif not isinstance(plan_data, dict):
                    raise MultiAgentOrchestrationError(
                        f"❌ Planner returned unsupported structure: {type(plan_data)}"
                    )
            except json.JSONDecodeError:
                plan_data = self._salvage_plan_data(content, str(planner_content))

            # Validate structure
            if "plan" not in plan_data:
                raise MultiAgentOrchestrationError(
                    f"❌ Plan must contain 'plan' key. Received: {list(plan_data.keys())}"
                )

            tasks = plan_data["plan"]

            if not isinstance(tasks, list):
                raise MultiAgentOrchestrationError(
                    f"❌ Plan must be a list. Received: {type(tasks)}"
                )

            if len(tasks) == 0:
                raise MultiAgentOrchestrationError(
                    "❌ Plan must contain at least one task."
                )

            # Validate each task
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    raise MultiAgentOrchestrationError(
                        f"❌ Task {i+1} must be a dictionary. Received: {type(task)}"
                    )

                if "id" not in task:
                    raise MultiAgentOrchestrationError(
                        f"❌ Task {i+1} missing 'id' field"
                    )

                if "description" not in task:
                    raise MultiAgentOrchestrationError(
                        f"❌ Task {i+1} missing 'description' field"
                    )

            # Return full plan_data (includes estimated_cycles and plan array)
            return plan_data

        except json.JSONDecodeError as e:
            raise MultiAgentOrchestrationError(
                f"❌ JSON parsing failed: {str(e)}\nContent:\n{str(planner_content)[:500]}"
            )
        except Exception as e:
            if isinstance(e, MultiAgentOrchestrationError):
                raise
            raise MultiAgentOrchestrationError(
                f"❌ Unexpected error parsing plan: {str(e)}"
            )

    def _salvage_plan_data(self, content: str, raw_output: str) -> Dict[str, Any]:
        """
        Recover valid tasks from a partially formed planner response.

        Attempts to decode individual task objects even if the JSON array is truncated.
        """
        plan_match = re.search(r'"plan"\s*:\s*\[', content)
        if not plan_match:
            raise MultiAgentOrchestrationError(
                f"❌ Cannot parse plan JSON. Planner output:\n{raw_output[:800]}"
            )

        decoder = json.JSONDecoder()
        idx = plan_match.end()
        tasks: List[Dict[str, Any]] = []

        while idx < len(content):
            # Skip whitespace and commas
            while idx < len(content) and content[idx] in " \t\r\n,":
                idx += 1

            if idx >= len(content) or content[idx] == ']':
                break

            try:
                obj, offset = decoder.raw_decode(content[idx:])
            except json.JSONDecodeError:
                # Stop on the first incomplete entry
                break

            if isinstance(obj, dict):
                tasks.append(obj)

            idx += offset

        if not tasks:
            raise MultiAgentOrchestrationError(
                f"❌ Planner response did not contain valid tasks.\n"
                f"Output snippet:\n{raw_output[:800]}"
            )

        plan_data: Dict[str, Any] = {"plan": tasks}

        estimated_cycles = self._extract_estimated_cycles_from_text(content)
        if estimated_cycles is not None:
            plan_data["estimated_cycles"] = estimated_cycles

        return plan_data

    @staticmethod
    def _extract_estimated_cycles_from_text(content: str) -> Optional[int]:
        """Extract estimated_cycles value from raw text."""
        match = re.search(r'"estimated_cycles"\s*:\s*(\d+)', content)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _duration_ms(start: Optional[datetime], end: Optional[datetime]) -> int:
        if not start or not end:
            return 0
        return max(int((end - start).total_seconds() * 1000), 0)

    def _append_event(
        self,
        *,
        event_type: str,
        cycle: int,
        agent: str,
        status: str,
        content: str,
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        duration_ms = None
        if started_at and completed_at:
            duration_ms = self._duration_ms(started_at, completed_at)

        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "cycle": cycle,
            "agent": agent,
            "status": status,
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_ms": duration_ms,
            "content": content,
            "metadata": metadata or {}
        }

        self.trace_events.append(event)

    def _extract_content(self, response: Any) -> str:
        """Extract text content from agent response."""
        if response is None:
            return ""

        def _safe_str(value: Any) -> str:
            return "" if value is None else str(value)

        if hasattr(response, "final_output"):
            final_output = getattr(response, "final_output")
            if final_output:
                return _safe_str(final_output)

        if hasattr(response, "content"):
            return _safe_str(getattr(response, "content"))

        if hasattr(response, "text"):
            return _safe_str(getattr(response, "text"))

        if isinstance(response, dict):
            for key in ("final_output", "content", "text", "output"):
                if key in response and response[key]:
                    return _safe_str(response[key])
            return str(response)

        return str(response)

    def _build_success_response(
        self,
        final_answer: str,
        plan_history: List[Dict],
        execution_log: List[Dict],
        agent_results: Dict[str, Any],
        cycles_used: int
    ) -> Dict[str, Any]:
        """Build successful response."""
        return {
            "success": True,
            "final_answer": final_answer,
            "plan_history": plan_history,
            "execution_log": execution_log,
            "agent_results": agent_results,
            "cycles_used": cycles_used,
            "trace": self.trace_events,
            "error": None,
            "timeout": False,
            "response": final_answer
        }

    def _build_error_response(
        self,
        error_msg: str,
        plan_history: List[Dict],
        execution_log: List[Dict],
        agent_results: Dict[str, Any],
        cycles_used: int
    ) -> Dict[str, Any]:
        """Build error response."""
        final_text = (
            f"❌ Error: {error_msg}\n\nPlease try rephrasing your question or check the system configuration."
        )
        return {
            "success": False,
            "final_answer": final_text,
            "plan_history": plan_history,
            "execution_log": execution_log,
            "agent_results": agent_results,
            "cycles_used": cycles_used,
            "trace": self.trace_events,
            "error": error_msg,
            "timeout": False,
            "response": final_text
        }

    def _build_timeout_response(
        self,
        plan_history: List[Dict],
        execution_log: List[Dict],
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build timeout response."""
        # Try to extract partial answer from last planner message
        last_planner_msg = next(
            (msg for msg in reversed(self.shared_history)
             if msg.get("agent") == "planner"),
            None
        )

        partial_answer = "⚠️ Maximum planning cycles reached. "

        if last_planner_msg:
            partial_answer += f"Last planner response:\n\n{last_planner_msg['content']}"
        else:
            partial_answer += "The task could not be completed within the allowed cycles. Please simplify your question."

        return {
            "success": False,
            "final_answer": partial_answer,
            "plan_history": plan_history,
            "execution_log": execution_log,
            "agent_results": agent_results,
            "cycles_used": self.max_cycles,
            "trace": self.trace_events,
            "error": None,
            "timeout": True,
            "response": partial_answer
        }
