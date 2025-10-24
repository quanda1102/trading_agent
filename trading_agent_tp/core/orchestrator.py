"""
Legacy Orchestrator

Basic planner-executor coordination for trading queries.
"""

import json
import re
from typing import List, Dict, Any, Optional
from agents import Runner

from .planner_agent import planner_agent
from .executor import executor_agent


class OrchestrationError(Exception):
    """Custom exception for orchestration errors."""
    pass


class PlannerExecutorOrchestrator:
    """Orchestrates the planner-executor loop for trading queries."""

    MAX_CYCLES = 3  # Maximum planning-execution cycles

    def __init__(self):
        """Initialize orchestrator with planner and executor."""
        self.runner = Runner()
        self.shared_history: List[Dict[str, Any]] = []

    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        memory_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query through planner-executor loop.

        Args:
            query: User's question
            user_id: User identifier
            session_id: Session identifier
            memory_context: Previous conversation context

        Returns:
            Dict with keys: final_answer, plan_history, execution_log, cycles_used
        """
        # Initialize shared history
        self.shared_history = []

        # Add memory context if available
        initial_query = query
        if memory_context:
            initial_query = f"Previous conversation:\n{memory_context}\n\nCurrent question: {query}"

        self.shared_history.append({
            "role": "user",
            "content": initial_query
        })

        plan_history = []
        execution_log = []

        try:
            # Prepare initial query with memory context
            initial_query = self._prepare_initial_query(query, memory_context)

            self.shared_history.append({
                "role": "user",
                "content": initial_query
            })

            # Planning-execution loop
            for cycle in range(self.MAX_CYCLES):
                print(f"\n{'='*80}")
                print(f"CYCLE {cycle + 1}/{self.MAX_CYCLES}")
                print(f"{'='*80}")

                # PHASE 1: PLANNING
                try:
                    plan_result = await self._planning_phase(cycle + 1)

                    # Check for final answer
                    if plan_result["is_final"]:
                        return self._build_success_response(
                            final_answer=plan_result["final_answer"],
                            plan_history=plan_history,
                            execution_log=execution_log,
                            cycles_used=cycle + 1
                        )

                    # Add plan to history
                    plan_history.append({
                        "cycle": cycle + 1,
                        "plan": plan_result["plan"]
                    })

                    print(f"\n📋 Plan Created: {len(plan_result['plan'])} tasks")

                except Exception as e:
                    error_msg = f"❌ Planning failed in cycle {cycle + 1}: {str(e)}"
                    print(error_msg)
                    return self._build_error_response(
                        error_msg=error_msg,
                        plan_history=plan_history,
                        execution_log=execution_log,
                        cycles_used=cycle + 1
                    )

                # PHASE 2: EXECUTION
                for task in plan_result["plan"]:
                    task_id = task["id"]
                    task_desc = task["description"]

                    print(f"\n🔧 Executing Task {task_id}: {task_desc}")

                    try:
                        exec_result = await self._execute_task(task)
                        execution_log.append({
                            "cycle": cycle + 1,
                            "task_id": task_id,
                            "task": task_desc,
                            "result": exec_result["result"],
                            "success": True
                        })

                        print(f"✅ Task {task_id} completed")
                        result_preview = exec_result['result'][:200]
                        print(f"Result preview: {result_preview}...")

                    except Exception as e:
                        error_result = f"❌ Task execution failed: {str(e)}"
                        execution_log.append({
                            "cycle": cycle + 1,
                            "task_id": task_id,
                            "task": task_desc,
                            "result": error_result,
                            "success": False
                        })

                        print(f"❌ Task {task_id} failed: {str(e)}")

                        # Add failure to shared history so planner can adapt
                        self.shared_history.append({
                            "role": "assistant",
                            "content": f"Task {task_id} result: {error_result}",
                            "agent": "executor",
                            "status": "failed"
                        })

            # Max cycles reached
            print(f"\n⚠️ Maximum cycles ({self.MAX_CYCLES}) reached")

            return self._build_timeout_response(
                plan_history=plan_history,
                execution_log=execution_log
            )

        except Exception as e:
            error_msg = f"❌ Orchestration error: {str(e)}"
            print(error_msg)
            return self._build_error_response(
                error_msg=error_msg,
                plan_history=plan_history,
                execution_log=execution_log,
                cycles_used=0
            )

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task using the executor agent."""
        task_desc = f"Task {task['id']}: {task['description']}"

        # Prepare input with context
        context_parts = [task_desc]

        # Include recent history for context
        for msg in self.shared_history[-3:]:  # Last 3 messages
            if msg.get("role") == "assistant":
                context_parts.append(f"Previous result: {msg['content'][:200]}...")

        executor_input = "\n".join(context_parts)

        # Run executor
        executor_response = await self.runner.run(executor_agent, executor_input)
        executor_content = self._extract_content(executor_response)

        # Add to shared history
        self.shared_history.append({
            "role": "assistant",
            "content": f"Task {task['id']} result: {executor_content}",
            "agent": "executor"
        })

        return {
            "result": executor_content
        }

    async def _planning_phase(self, cycle_num: int) -> Dict[str, Any]:
        """Execute planning phase."""
        # Format history for planner
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

        # Check for final answer
        content_cleaned = planner_content.strip()

        # Remove markdown code fences if present
        if content_cleaned.startswith("```"):
            content_cleaned = re.sub(r'^```(?:json|markdown)?\s*', '', content_cleaned)
            content_cleaned = re.sub(r'\s*```$', '', content_cleaned)
            content_cleaned = content_cleaned.strip()

        # Check for final answer
        if "FINAL ANSWER:" in content_cleaned.upper():
            # Find the final answer marker (case-insensitive)
            final_marker_match = re.search(r'FINAL\s+ANSWER\s*:', content_cleaned, re.IGNORECASE)
            if final_marker_match:
                final_answer = content_cleaned[final_marker_match.end():].strip()
                return {
                    "is_final": True,
                    "final_answer": final_answer
                }

        # Parse plan
        plan = self._parse_plan(planner_content)

        return {
            "is_final": False,
            "plan": plan
        }

    def _parse_plan(self, planner_content: str) -> List[Dict[str, Any]]:
        """Parse JSON plan from planner response."""
        try:
            # Remove markdown code fences
            content = planner_content.strip()
            content = re.sub(r'^```json?\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()

            # Try to find JSON object
            json_match = re.search(r'\{.*?"plan"\s*:\s*\[.*', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

            # Attempt to balance braces/brackets for truncated output
            if content.count('{') > content.count('}'):
                content += '}' * (content.count('{') - content.count('}'))

            if content.count('[') > content.count(']'):
                content += ']' * (content.count('[') - content.count(']'))

            # Parse JSON
            try:
                plan_data = json.loads(content)
                if isinstance(plan_data, list):
                    plan_data = {"plan": plan_data}
                elif not isinstance(plan_data, dict):
                    raise OrchestrationError(
                        f"❌ Planner returned unsupported structure: {type(plan_data)}"
                    )
            except json.JSONDecodeError:
                plan_data = self._salvage_plan_data(content, str(planner_content))

            # Validate structure
            if "plan" not in plan_data:
                raise OrchestrationError(
                    f"❌ Plan must contain 'plan' key. Received: {list(plan_data.keys())}"
                )

            tasks = plan_data["plan"]

            if not isinstance(tasks, list):
                raise OrchestrationError(
                    f"❌ Plan must be a list. Received: {type(tasks)}"
                )

            if len(tasks) == 0:
                raise OrchestrationError(
                    "❌ Plan must contain at least one task."
                )

            # Validate each task
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    raise OrchestrationError(
                        f"❌ Task {i+1} must be a dictionary. Received: {type(task)}"
                    )

                if "id" not in task:
                    raise OrchestrationError(
                        f"❌ Task {i+1} missing 'id' field"
                    )

                if "description" not in task:
                    raise OrchestrationError(
                        f"❌ Task {i+1} missing 'description' field"
                    )

            return tasks

        except json.JSONDecodeError as e:
            raise OrchestrationError(
                f"❌ JSON parsing failed: {str(e)}\nContent:\n{planner_content[:500]}"
            )
        except Exception as e:
            if isinstance(e, OrchestrationError):
                raise
            raise OrchestrationError(
                f"❌ Unexpected error parsing plan: {str(e)}"
            )

    def _salvage_plan_data(self, content: str, raw_output: str) -> Dict[str, Any]:
        """
        Recover valid tasks from partially formed planner output.
        """
        plan_match = re.search(r'"plan"\s*:\s*\[', content)
        if not plan_match:
            raise OrchestrationError(
                f"❌ Cannot parse plan JSON. Planner output:\n{raw_output[:800]}"
            )

        decoder = json.JSONDecoder()
        idx = plan_match.end()
        tasks: List[Dict[str, Any]] = []

        while idx < len(content):
            while idx < len(content) and content[idx] in " \t\r\n,":
                idx += 1

            if idx >= len(content) or content[idx] == ']':
                break

            try:
                obj, offset = decoder.raw_decode(content[idx:])
            except json.JSONDecodeError:
                break

            if isinstance(obj, dict):
                tasks.append(obj)

            idx += offset

        if not tasks:
            raise OrchestrationError(
                f"❌ Planner response did not contain valid tasks.\n"
                f"Output snippet:\n{raw_output[:800]}"
            )

        return {"plan": tasks}

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
                elif agent == "executor":
                    messages.append(f"Executor{status_marker}: {content}")
                else:
                    messages.append(f"Assistant{status_marker}: {content}")

        return "\n\n".join(messages)

    def _build_success_response(
        self,
        final_answer: str,
        plan_history: List[Dict],
        execution_log: List[Dict],
        cycles_used: int
    ) -> Dict[str, Any]:
        """Build successful response."""
        return {
            "success": True,
            "final_answer": final_answer,
            "plan_history": plan_history,
            "execution_log": execution_log,
            "cycles_used": cycles_used,
            "error": None,
            "timeout": False
        }

    def _build_error_response(
        self,
        error_msg: str,
        plan_history: List[Dict],
        execution_log: List[Dict],
        cycles_used: int
    ) -> Dict[str, Any]:
        """Build error response."""
        return {
            "success": False,
            "final_answer": f"❌ Error: {error_msg}\n\nPlease try rephrasing your question or check the system configuration.",
            "plan_history": plan_history,
            "execution_log": execution_log,
            "cycles_used": cycles_used,
            "error": error_msg,
            "timeout": False
        }

    def _build_timeout_response(
        self,
        plan_history: List[Dict],
        execution_log: List[Dict]
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
            "cycles_used": self.MAX_CYCLES,
            "error": None,
            "timeout": True
        }
