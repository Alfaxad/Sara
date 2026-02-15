import json
import operator
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage
from langchain_core.tools import render_text_description
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from modules.tools import (
    get_patient_data_manifest,
    get_patient_fhir_resource,
)

_LLM_INVOKE_ARGS = {"max_tokens": 8000, "temperature": 0.6}


def exclude_thinking_component(text: str) -> str:
  """Removes the thinking block (delimited by <unused94> and <unused95>) from a string."""
  return re.sub(r"<unused94>.*?<unused95>", "", text, flags=re.DOTALL).strip()


def strip_json_decoration(text: str) -> str:
  """Removes JSON markdown fences from the start and end of a string."""
  match = re.search(r"```(?:json)?\s*([\{\[].*[\]\}])\s*```", text, re.DOTALL)
  if match:
    return match.group(1)
  return text.strip()


class AgentState(TypedDict):
  messages: Annotated[list, operator.add]
  patient_fhir_manifest: dict
  tool_output_summary: Annotated[list, operator.add]
  tool_calls_to_execute: Annotated[list, operator.add]
  relevant_resource_types: list
  manifest_tool_call_request: AIMessage
  sdt_idx: int
  edr_idx: int
  resource_type_processed: str
  resource_type_retrieved: str
  summary_generated: bool
  resource_type_to_retrieve: str
  resource_type_to_process: str
  fhir_tool_output: str
  resource_being_summarized: str
  tool_call: dict
  resource_manifest_codes: list


def create_agent(llm, fhir_store_url):
  """Creates and compiles the LangGraph agent."""

  manifest_tool_node = ToolNode([get_patient_data_manifest])
  data_retrieval_tool_node = ToolNode([get_patient_fhir_resource])

  def generate_manifest_tool_call_node(state):
    """The first step: uses the LLM to find the patient_id from the initial question

    and generates a tool call for get_patient_data_manifest.
    """
    last_message = state["messages"][-1]
    extraction_prompt = (
        f"USER QUESTION: {last_message.content}\\n\\nYou are an API request"
        " generator. Your task is to identify the patient ID from the user's"
        " question and output a JSON object to call the"
        " `get_patient_data_manifest` tool.\\n\\nYour available tool"
        f" is:\\n{render_text_description([get_patient_data_manifest])}\\n\\nGenerate"
        " the correct JSON to call the tool. Respond with only a single, raw"
        ' JSON object.\\n\\nEXAMPLE:\\n{\\n  "name":'
        ' "get_patient_data_manifest",\\n  "args": {\\n    "patient_id":'
        ' "some-patient-id-from-the-question"\\n  }\\n}\\n'
    )
    print(
        "--- generate_manifest_tool_call_node PROMPT"
        f" ---\n{extraction_prompt}\n-----------------------------"
    )
    response_str = llm.invoke(extraction_prompt, **_LLM_INVOKE_ARGS)
    print(
        "--- generate_manifest_tool_call_node RESPONSE"
        f" ---\n{response_str}\n------------------------------"
    )
    try:
      cleaned_response = strip_json_decoration(response_str)
      tool_call_json = json.loads(cleaned_response)
      tool_call_json["args"]["fhir_store_url"] = fhir_store_url
      tool_call_msg = AIMessage(
          content="",
          tool_calls=[{**tool_call_json, "id": "manifest_call"}],
      )
      return {
          "manifest_tool_call_request": tool_call_msg,
          "tool_call": tool_call_json,
      }
    except Exception as e:
      print(f"Error generating manifest tool call: {e}")
      raise e

  def execute_manifest_tool_call_node(state):
    """Executes the get_patient_data_manifest tool call and puts the result in state."""
    try:
      tool_call_msg = state["manifest_tool_call_request"]
      tool_output_message = manifest_tool_node.invoke([tool_call_msg])[0]
      manifest_dict = json.loads(tool_output_message.content)
      print(f"Manifest dict: {manifest_dict}")
      return {"patient_fhir_manifest": manifest_dict}
    except Exception as e:
      print(f"Error calling manifest tool: {e}")
      raise e

  def identify_relevant_resource_types(state):
    """Uses the manifest and user question to identify relevant FHIR resource types."""
    print("Identifying Relevant Resource Types")
    manifest = state.get("patient_fhir_manifest", {})
    user_question = state["messages"][1].content
    manifest_content = ""
    for resource_type, codes in manifest.items():
      manifest_content += f"**{resource_type}**: "
      if codes:
        manifest_content += f"Available codes include: {', '.join(codes)}\\n"
      else:
        manifest_content += "Present (no specific codes found)\\n"
    prompt = (
        "SYSTEM INSTRUCTION: think silently if needed.\\nUSER QUESTION:"
        f" {user_question}\\n\\nPATIENT DATA"
        f" MANIFEST:\\n{manifest_content}\\n\\nYou are a medical assistant"
        " analyzing a patient's FHIR data manifest to answer a user"
        " question.\\nBased on the user question, identify the specific FHIR"
        " resource types from the manifest that are most likely to contain the"
        " information needed to answer the question.\\nOutput a JSON list of"
        " the relevant resource types. Do not include any other text or"
        ' formatting.\\nExample:\n["Condition", "Observation",'
        ' "MedicationRequest"]\n'
    )
    print(
        "--- identify_relevant_resource_types PROMPT"
        f" ---\n{prompt}\n------------------------------------------"
    )
    response_str = llm.invoke(prompt, **_LLM_INVOKE_ARGS)
    print(
        "--- identify_relevant_resource_types RESPONSE"
        f" ---\n{response_str}\n-------------------------------------------"
    )
    try:
      relevant_resource_types = json.loads(strip_json_decoration(response_str))
    except json.JSONDecodeError:
      print(
          "Could not decode JSON response for relevant resource types:"
          f" {response_str}"
      )
      relevant_resource_types = []
    print(
        "Relevant Resource Types Identified:"
        f" {', '.join(relevant_resource_types)}"
    )
    return {
        "relevant_resource_types": relevant_resource_types,
        "sdt_idx": 0,
        "tool_calls_to_execute": [],
    }

  def announce_sdt_node(state):
    sdt_idx = state["sdt_idx"]
    relevant_resource_types = state.get("relevant_resource_types", [])
    resource_type = relevant_resource_types[sdt_idx]
    manifest = state.get("patient_fhir_manifest", {})
    resource_manifest = manifest.get(resource_type, [])
    print(f"Announcing data selection for {resource_type}")
    return {
        "resource_type_to_process": resource_type,
        "resource_manifest_codes": resource_manifest,
    }

  def select_data_to_retrieve(state):
    """Uses the manifest and relevant resource types to determine which FHIR resources to retrieve."""
    sdt_idx = state["sdt_idx"]
    manifest = state.get("patient_fhir_manifest", {})
    relevant_resource_types = state.get("relevant_resource_types", [])
    tools_string = render_text_description([get_patient_fhir_resource])

    resource_type = relevant_resource_types[sdt_idx]
    print(f"Data Selection for {resource_type}")

    if resource_type not in manifest:
      print(f"No data found for {resource_type} in the manifest.")
      return {"sdt_idx": sdt_idx + 1, "resource_type_processed": resource_type}

    manifest_content = f"**{resource_type}**: "
    if len(manifest.get(resource_type, [])) > 0:
      manifest_content += (
          f"Available codes include: {', '.join(manifest[resource_type])}\\n"
      )
    else:
      manifest_content += "Present (no specific codes found)\\n"
    prompt = (
        "SYSTEM INSTRUCTION: think silently if needed.\\n"
        + "FOR CONTEXT ONLY, USER QUESTION:"
        f" {state['messages'][1].content}\\n\\n"
        + f"PATIENT DATA MANIFEST: {manifest_content}\\n\\n"
        + "You are a specialized API request generator. Your SOLE task is to"
        " output a JSON of a tool call to gather the necessary information"
        " to answer the user's question. Respond with ONLY a JSON, no"
        " explanations or prose.\\n"
        + f"Your available tool is:\\n{tools_string}\\n\\n"
        + f"**At this stage you can only call {resource_type}.**\\n"
        + "EXAMPLE:\\n"
        + '{\\"name\\": \\"get_patient_fhir_resource\\", \\"args\\":'
        ' {\\"patient_id\\": \\"some-patient-id\\",'
        ' \\"fhir_resource\\": \\"'
        + resource_type
        + '\\", \\"filter_code\\": \\"csv-codes-from-manifest\\"}}'
    )
    print(
        f"--- select_data_to_retrieve PROMPT ({resource_type})"
        f" ---\n{prompt}\n------------------------------------------"
    )
    response_str = llm.invoke(prompt, **_LLM_INVOKE_ARGS)
    print(
        f"--- select_data_to_retrieve RESPONSE ({resource_type})"
        f" ---\n{response_str}\n-------------------------------------------"
    )
    try:
      tool_call = json.loads(strip_json_decoration(response_str))
      tool_call["args"]["fhir_store_url"] = fhir_store_url
      return {
          "tool_calls_to_execute": [{**tool_call, "id": resource_type}],
          "sdt_idx": sdt_idx + 1,
          "resource_type_processed": resource_type,
      }
    except json.JSONDecodeError:
      print(
          f"Could not decode JSON response for {resource_type}: {response_str}"
      )
      # If we fail to decode, we just skip this resource type.
      return {"sdt_idx": sdt_idx + 1, "resource_type_processed": resource_type}

  def sdt_conditional_edge(state):
    if state["sdt_idx"] < len(state["relevant_resource_types"]):
      return "announce_sdt"
    return "init_edr_idx"

  def init_edr_idx_node(state):
    return {"edr_idx": 0}

  def init_edr_conditional_edge(state):
    if state["tool_calls_to_execute"]:
      return "announce_retrieval"
    return "final_answer"

  def announce_retrieval_node(state):
    edr_idx = state["edr_idx"]
    tool_calls = state.get("tool_calls_to_execute", [])
    tool_call = tool_calls[edr_idx]
    resource_type = tool_call.get("id", "unknown_resource")
    print(f"Announcing retrieval of {resource_type}")
    return {"resource_type_to_retrieve": resource_type}

  def execute_data_retrieval(state):
    """Executes the planned tool calls and summarizes the output."""
    edr_idx = state["edr_idx"]
    tool_calls = state.get("tool_calls_to_execute", [])
    tool_call = tool_calls[edr_idx]
    resource_type = tool_call.get("id", "unknown_resource")
    print(f"Fetching FHIR data for {resource_type}")
    tool_output_list = data_retrieval_tool_node.invoke(
        [AIMessage(content="", tool_calls=[tool_call])]
    )
    if not tool_output_list:
      print(f"No tool output received for {resource_type}")
      return {
          "resource_type_retrieved": resource_type,
          "summary_generated": False,
          "fhir_tool_output": "",
      }

    tool_output = tool_output_list[0].content
    return {
        "resource_type_retrieved": resource_type,
        "summary_generated": True,
        "fhir_tool_output": tool_output,
    }

  def announce_summarization_node(state):
    resource_type = state["resource_type_retrieved"]
    print(f"Announcing summarization of {resource_type}")
    return {"resource_being_summarized": resource_type}

  def summarize_node(state: AgentState) -> dict:
    if not state["summary_generated"]:
      return {"edr_idx": state["edr_idx"] + 1}

    resource_type = state["resource_type_retrieved"]
    tool_output = state["fhir_tool_output"]
    concise_facts_prompt = (
        "SYSTEM INSTRUCTION: think silently if needed.\\nFOR CONTEXT ONLY,"
        f" USER QUESTION: {state['messages'][1].content}\\n\\nTOOL"
        f" OUTPUT:\\n{tool_output}\\n\\nYou are a fact summarizing agent."
        " Your output will be used to answer the USER QUESTION.\\nCollect"
        " from the 'TOOL OUTPUT' facts ONLY if it is relevant to answer the"
        " USER QUESTION.\\nWrite a very concise English summary, only facts"
        " relevant to the user question. DO NOT OUTPUT JSON.\\nYou are not"
        " authorized to answer the user question. Do not provide any output"
        " beyond concise facts. Filter out any facts which are not helpful"
        " for the user question. Include date or date ranges. Only for the"
        " most critical facts, include FHIR record references [record"
        " type/record id]. For repeating multiple times provide summarize"
        " and provide only a single reference and date range."
    )
    print(
        f"--- summarize_node PROMPT ({resource_type})"
        f" ---\n{concise_facts_prompt}\n------------------------------------------"
    )
    current_summary = llm.invoke(concise_facts_prompt, **_LLM_INVOKE_ARGS)
    print(
        f"--- summarize_node RESPONSE ({resource_type})"
        f" ---\n{current_summary}\n-------------------------------------------"
    )
    return {
        "tool_output_summary": [exclude_thinking_component(current_summary)],
        "edr_idx": state["edr_idx"] + 1,
        "resource_type_retrieved": resource_type,
    }

  def should_summarize_edge(state):
    if state["summary_generated"]:
      return "announce_summarization"
    return "summarize_node"

  def edr_conditional_edge(state):
    if state["edr_idx"] < len(state["tool_calls_to_execute"]):
      return "announce_retrieval"
    return "final_answer"

  def get_final_answer(state):
    """If we have enough data, this node generates the final answer."""
    summary = "\\n\\n".join(state["tool_output_summary"])
    prompt = (
        "Synthesize all information from the 'SUMMARIZED INFORMATION' to"
        " provide a comprehensive final answer. Preserve relevant FHIR"
        " references.\\n\\nUSER QUESTION:"
        f" {state['messages'][1].content}\\n\\nSUMMARIZED INFORMATION:"
        f" {summary}\\n\\nFinal Answer using markdown:"
    )
    print(
        "--- get_final_answer PROMPT"
        f" ---\n{prompt}\n------------------------------------------"
    )
    response = llm.invoke(prompt, **_LLM_INVOKE_ARGS)
    print(
        "--- get_final_answer RESPONSE"
        f" ---\n{response}\n-------------------------------------------"
    )
    return {"messages": [AIMessage(content=response)]}

  workflow = StateGraph(AgentState)
  workflow.add_node(
      "generate_manifest_tool_call", generate_manifest_tool_call_node
  )
  workflow.add_node(
      "execute_manifest_tool_call", execute_manifest_tool_call_node
  )
  workflow.add_node(
      "identify_relevant_resource_types", identify_relevant_resource_types
  )
  workflow.add_node("announce_sdt", announce_sdt_node)
  workflow.add_node("select_data_to_retrieve", select_data_to_retrieve)
  workflow.add_node("init_edr_idx", init_edr_idx_node)
  workflow.add_node("announce_retrieval", announce_retrieval_node)
  workflow.add_node("execute_data_retrieval", execute_data_retrieval)
  workflow.add_node("announce_summarization", announce_summarization_node)
  workflow.add_node("summarize_node", summarize_node)
  workflow.add_node("final_answer", get_final_answer)
  workflow.set_entry_point("generate_manifest_tool_call")
  workflow.add_edge("generate_manifest_tool_call", "execute_manifest_tool_call")
  workflow.add_edge(
      "execute_manifest_tool_call", "identify_relevant_resource_types"
  )
  workflow.add_edge(
      "identify_relevant_resource_types", "announce_sdt"
  )
  workflow.add_edge("announce_sdt", "select_data_to_retrieve")
  workflow.add_conditional_edges(
      "select_data_to_retrieve",
      sdt_conditional_edge,
      {
          "announce_sdt": "announce_sdt",
          "init_edr_idx": "init_edr_idx",
      },
  )
  workflow.add_conditional_edges(
      "init_edr_idx",
      init_edr_conditional_edge,
      {
          "announce_retrieval": "announce_retrieval",
          "final_answer": "final_answer",
      },
  )
  workflow.add_edge("announce_retrieval", "execute_data_retrieval")
  workflow.add_conditional_edges(
      "execute_data_retrieval",
      should_summarize_edge,
      {
          "announce_summarization": "announce_summarization",
          "summarize_node": "summarize_node",
      },
  )
  workflow.add_edge("announce_summarization", "summarize_node")
  workflow.add_conditional_edges(
      "summarize_node",
      edr_conditional_edge,
      {
          "announce_retrieval": "announce_retrieval",
          "final_answer": "final_answer",
      },
  )
  workflow.add_edge("final_answer", END)
  return workflow.compile()
