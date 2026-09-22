"""
ReAct Agent Core for SmartAGENT.
Implements the Thought → Action → Observation reasoning loop powered by Fluxnat Coder 3B.
"""

import re
import time
from typing import Optional, Generator, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

from smartagent.agent.memory import AgentMemory
from smartagent.agent.tools import ToolRegistry
from smartagent.agent.prompts import (
    AGENT_SYSTEM_PROMPT,
    REACT_OBSERVATION_PREFIX,
    REACT_CONTINUE_PROMPT,
)

console = Console(legacy_windows=False)


class SmartAgent:
    """
    Autonomous security agent using a ReAct reasoning loop.

    The agent thinks step-by-step, calls tools, observes results,
    and continues until it has a Final Answer.
    """

    def __init__(
        self,
        model_id: str = "k4ran909/Fluxnat-Coder-3B",
        working_dir: str = ".",
        max_iterations: int = 15,
        temperature: float = 0.3,
        verbose: bool = True,
    ):
        self.model_id = model_id
        self.working_dir = working_dir
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.verbose = verbose

        self.tools = ToolRegistry(working_dir=working_dir)
        self.memory = AgentMemory(max_messages=20)
        self._model_manager = None  # lazy loaded

    @property
    def model_manager(self):
        """Lazy-load the model to avoid slow startup when not needed."""
        if self._model_manager is None:
            from smartagent.ai.model import ModelManager
            self._model_manager = ModelManager.get_instance(
                model_id=self.model_id, load_in_4bit=True
            )
        return self._model_manager

    def run(self, user_message: str) -> str:
        """
        Run the full agent loop for a single user message.
        Returns the final answer string.
        """
        # Build system prompt with tool descriptions
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            tool_descriptions=self.tools.get_tool_descriptions()
        )

        # Initialize memory for this run if it's the first message
        if not self.memory.messages:
            self.memory.add_message("system", system_prompt)

        # Add the user message
        self.memory.add_message("user", user_message)

        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                console.print(
                    f"  [dim]⟳ Step {iteration}/{self.max_iterations}[/dim]",
                    highlight=False,
                )

            # Generate LLM response
            messages = self.memory.get_messages()
            try:
                llm_output = self.model_manager.generate(
                    messages,
                    max_tokens=512,
                    temperature=self.temperature,
                )
            except Exception as e:
                error_msg = f"Model inference error: {e}"
                if self.verbose:
                    console.print(f"  [red]✗ {error_msg}[/red]")
                return f"Error: {error_msg}"

            llm_output = llm_output.strip()

            # Parse the output
            thought, action, action_input, final_answer = self._parse_output(llm_output)

            # Display thought
            if thought and self.verbose:
                console.print(
                    Panel(
                        thought,
                        title="[bold cyan]💭 Thought[/bold cyan]",
                        border_style="cyan",
                        expand=False,
                    )
                )

            # Case 1: Final Answer — we're done
            if final_answer is not None:
                self.memory.add_message("assistant", llm_output)
                if self.verbose:
                    console.print(
                        Panel(
                            final_answer,
                            title="[bold green]✅ Final Answer[/bold green]",
                            border_style="green",
                        )
                    )
                return final_answer

            # Case 2: Tool call
            if action and action_input is not None:
                if self.verbose:
                    console.print(
                        f"  [yellow]⚡ Action:[/yellow] {action}({action_input[:80]}{'...' if len(action_input) > 80 else ''})"
                    )

                # Execute the tool
                observation = self.tools.execute(action, action_input)

                if self.verbose:
                    # Show truncated observation
                    obs_display = observation[:300] + "..." if len(observation) > 300 else observation
                    console.print(
                        Panel(
                            obs_display,
                            title=f"[bold yellow]📋 Observation ({action})[/bold yellow]",
                            border_style="yellow",
                            expand=False,
                        )
                    )

                # Add assistant output + observation to memory
                self.memory.add_message("assistant", llm_output)
                self.memory.add_message(
                    "user",
                    f"{REACT_OBSERVATION_PREFIX}{observation}\n\n{REACT_CONTINUE_PROMPT}",
                )
                continue

            # Case 3: Malformed output — the model didn't follow format
            if self.verbose:
                console.print(f"  [dim red]⚠ Malformed output, nudging model...[/dim red]")

            self.memory.add_message("assistant", llm_output)
            self.memory.add_message(
                "user",
                "Your response was not in the correct format. "
                "You MUST respond with either:\n"
                "1. Thought: ... then Action: ... and Action Input: ...\n"
                "2. Thought: ... then Final Answer: ...\n\n"
                "Please try again.",
            )

        # Max iterations reached
        exhausted_msg = (
            "I reached the maximum number of reasoning steps. "
            f"Here's what I found so far:\n\n{self.memory.get_findings_summary()}"
        )
        if self.verbose:
            console.print(f"  [red]⚠ Max iterations ({self.max_iterations}) reached.[/red]")
        return exhausted_msg

    def chat(self, user_message: str) -> str:
        """
        Chat-style interface. Preserves memory across calls.
        """
        return self.run(user_message)

    def reset(self):
        """Clear all memory and start fresh."""
        self.memory.clear()

    # ------------------------------------------------------------------
    # ReAct output parser
    # ------------------------------------------------------------------

    def _parse_output(self, text: str) -> Tuple[
        Optional[str],  # thought
        Optional[str],  # action
        Optional[str],  # action_input
        Optional[str],  # final_answer
    ]:
        """
        Parse LLM output into (thought, action, action_input, final_answer).
        Returns (thought, None, None, final_answer) if Final Answer found.
        Returns (thought, action, action_input, None) if Action found.
        Returns (thought, None, None, None) if neither found (malformed).
        """
        thought = None
        action = None
        action_input = None
        final_answer = None

        # Extract thought
        thought_match = re.search(
            r"Thought:\s*(.*?)(?=\n(?:Action:|Final Answer:)|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if thought_match:
            thought = thought_match.group(1).strip()

        # Check for Final Answer first (takes priority)
        final_match = re.search(
            r"Final Answer:\s*(.*)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if final_match:
            final_answer = final_match.group(1).strip()
            return thought, None, None, final_answer

        # Check for Action + Action Input
        action_match = re.search(
            r"Action:\s*(\S+)",
            text,
            re.IGNORECASE,
        )
        input_match = re.search(
            r"Action Input:\s*(.*?)(?=\n(?:Thought:|Action:|Final Answer:|Observation:)|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if action_match:
            action = action_match.group(1).strip()
        if input_match:
            action_input = input_match.group(1).strip()
        elif action:
            # If action found but no explicit Action Input, use empty string
            action_input = ""

        return thought, action, action_input, final_answer
