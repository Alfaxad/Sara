"""
Sara Agent Core

The hybrid ADK agent that orchestrates Sara's multi-turn workflow with event streaming.
Takes clinical tasks, calls the Sara model, parses actions, executes FHIR calls,
and yields events for streaming to the frontend.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List

from openai import AsyncOpenAI

from modal.utils.fhir_client import FHIRClient, FHIRResult
from modal.utils.parser import parse_action, ActionType

# Maximum agent iterations before giving up
MAX_ROUNDS = 8


@dataclass
class AgentEvent:
    """Event emitted by the Sara agent during execution."""
    type: str  # "thinking", "tool_call", "complete", "error"
    timestamp: float
    content: str = ""  # For thinking events (Sara's response)
    tool: str = ""  # For tool_call events (GET/POST)
    result: Any = None  # Tool result or final answer


# MedAgentBench-style prompt template
MEDAGENTBENCH_PROMPT = """You are an expert in using FHIR functions to assist medical professionals. You are given a question and a set of possible functions. Based on the question, you may need to make one or more function calls to get the information needed or to take actions.

1. If you decide to invoke a GET function, you MUST put it in the format of
GET url?param_name1=param_value1&param_name2=param_value2...

2. If you decide to invoke a POST function, you MUST put it in the format of
POST url
[your payload data in JSON format]

3. If you have got answers for all the questions and finished all the requested tasks, you MUST call to finish the conversation in the format of
FINISH([answer1, answer2, ...])

Here is a list of functions in JSON format that you can invoke. Note that you should use {api_base} as the api_base.
{functions}

Context: {context}
Question: {question}"""


class SaraAgent:
    """
    Custom agent that handles Sara's text-based tool calling.

    Orchestrates the multi-turn workflow:
    1. Takes a clinical task
    2. Calls the Sara model which outputs GET/POST/FINISH actions
    3. Parses the action using the parser
    4. Executes FHIR calls using the FHIR client
    5. Injects results back into context for the next round
    6. Yields events for streaming to the frontend
    7. Continues until FINISH or max rounds reached
    """

    def __init__(self, sara_url: str, fhir_url: str, functions: List[Dict]):
        """
        Initialize the Sara agent.

        Args:
            sara_url: Base URL of the Sara model service (OpenAI-compatible API)
            fhir_url: Base URL of the FHIR server
            functions: List of FHIR function definitions for the prompt
        """
        self.sara_url = sara_url
        self.fhir_url = fhir_url
        self.functions = functions
        self._sara_client = AsyncOpenAI(
            base_url=f"{sara_url}/v1",
            api_key="not-needed"  # Sara model doesn't require auth
        )

    def _build_prompt(self, context: str, question: str) -> str:
        """
        Build the MedAgentBench-style prompt.

        Args:
            context: Clinical context for the task
            question: The question or task to complete

        Returns:
            Formatted prompt string
        """
        functions_str = json.dumps(self.functions, indent=2)
        return MEDAGENTBENCH_PROMPT.format(
            api_base=self.fhir_url,
            functions=functions_str,
            context=context,
            question=question
        )

    async def _call_sara(self, messages: List[Dict]) -> str:
        """
        Call the Sara model via OpenAI-compatible API.

        Args:
            messages: List of chat messages

        Returns:
            Model response content as string
        """
        response = await self._sara_client.chat.completions.create(
            model="sara",  # Model name doesn't matter for vLLM
            messages=messages,
            temperature=0.0,
            max_tokens=2048
        )
        return response.choices[0].message.content

    def _format_fhir_result(self, result: FHIRResult) -> str:
        """
        Format a FHIR result for injection into the conversation context.

        Args:
            result: FHIRResult from the FHIR client

        Returns:
            Formatted string representation of the result
        """
        if result.success:
            return json.dumps(result.data, indent=2)
        else:
            return f"Error (HTTP {result.status_code}): {result.error}"

    async def run(
        self,
        context: str,
        question: str
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Run the agent loop.

        Yields events as the agent progresses through the task:
        - "thinking": Sara's response
        - "tool_call": FHIR call execution
        - "complete": Task finished with answer
        - "error": Something went wrong

        Args:
            context: Clinical context for the task
            question: The question or task to complete

        Yields:
            AgentEvent objects representing progress
        """
        # Build initial prompt
        initial_prompt = self._build_prompt(context, question)
        messages = [{"role": "user", "content": initial_prompt}]

        # Initialize FHIR client
        fhir_client = FHIRClient(self.fhir_url)

        try:
            for round_num in range(MAX_ROUNDS):
                # 1. Call Sara
                try:
                    response = await self._call_sara(messages)
                except Exception as e:
                    yield AgentEvent(
                        type="error",
                        content=f"Sara model error: {str(e)}",
                        timestamp=time.time()
                    )
                    return

                # Yield thinking event
                yield AgentEvent(
                    type="thinking",
                    content=response,
                    timestamp=time.time()
                )

                # 2. Parse the action
                action = parse_action(response)

                # 3. Handle FINISH action
                if action.type == ActionType.FINISH:
                    yield AgentEvent(
                        type="complete",
                        result=action.answer,
                        timestamp=time.time()
                    )
                    return

                # 4. Handle UNKNOWN action
                if action.type == ActionType.UNKNOWN:
                    # Inject the unknown response and let Sara try again
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": "Your response did not contain a valid action. Please use GET, POST, or FINISH format."
                    })
                    continue

                # 5. Execute FHIR call (GET or POST)
                fhir_result = await fhir_client.execute(action)

                # Yield tool_call event
                yield AgentEvent(
                    type="tool_call",
                    tool=action.type.value,
                    result=fhir_result.data if fhir_result.success else {
                        "error": fhir_result.error,
                        "status_code": fhir_result.status_code
                    },
                    timestamp=time.time()
                )

                # 6. Inject result into context
                formatted_result = self._format_fhir_result(fhir_result)
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Result: {formatted_result}"})

            # Reached max rounds without FINISH
            yield AgentEvent(
                type="error",
                content=f"Agent reached maximum rounds ({MAX_ROUNDS}) without completing the task.",
                timestamp=time.time()
            )

        finally:
            # Always close the FHIR client
            await fhir_client.close()
