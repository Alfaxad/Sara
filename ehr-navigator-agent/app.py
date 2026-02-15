import os
from flask import Flask, Response, jsonify, render_template, request, send_file
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import VertexAIModelGarden
from modules.agent import create_agent

app = Flask(__name__)

# --- Configuration ---
import re
import json

llm_endpoint = os.environ.get("LLM_ENDPOINT")
if llm_endpoint:
  match = re.search(
      r"projects/([^/]+)/locations/([^/]+)/endpoints/([^/]+)", llm_endpoint
  )
  if match:
    YOUR_PROJECT_ID, YOUR_REGION, YOUR_ENDPOINT_ID = match.groups()
  else:
    YOUR_PROJECT_ID = os.environ.get("YOUR_PROJECT_ID")
    YOUR_REGION = os.environ.get("YOUR_REGION", "us-central1")
    YOUR_ENDPOINT_ID = os.environ.get("YOUR_ENDPOINT_ID", "1030")
else:
  YOUR_PROJECT_ID = os.environ.get("YOUR_PROJECT_ID")
  YOUR_REGION = os.environ.get("YOUR_REGION", "us-central1")
  YOUR_ENDPOINT_ID = os.environ.get("YOUR_ENDPOINT_ID", "1030")
FHIR_STORE_URL = os.environ.get("FHIR_STORE_URL")

# --- Hardcoded Questions ---
PREDEFINED_QUESTIONS = [
    {
        "id": "q1",
        "question": (
            "What were the results and dates of the patient's lastest "
            "lipid panel and CBC tests?"
        ),
        "patient_id": "c1ae6e14-1833-a8e2-8e26-e0508236994a",
    },
    {
        "id": "q2",
        "question": (
            "What specific medications were administered to the patient during"
            " their sepsis encounter?"
        ),
        "patient_id": "e4350e97-bb8c-70b7-9997-9e098cfacef8",
    },
]

# --- LLM and Agent Initialization ---
try:
  import google.auth
  from langchain_community.cache import SQLiteCache
  from langchain_core.globals import set_llm_cache

  if os.environ.get("SERVICE_ACC_KEY"):
    credentials, project_id = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/cloud-healthcare",
        ]
    )
    llm = VertexAIModelGarden(
        project=YOUR_PROJECT_ID or project_id,
        location=YOUR_REGION,
        endpoint_id=YOUR_ENDPOINT_ID,
        credentials=credentials,
        allowed_model_args=["temperature", "max_tokens"],
    )
  else:
    from langchain_core.language_models.fake import FakeListLLM
    responses = [
        '{"name": "get_patient_data_manifest", "args": {"patient_id": "c1ae6e14-1833-a8e2-8e26-e0508236994a"}}',
        '[]',
        'Dummy answer'
    ]
    llm = FakeListLLM(responses=responses)
    print("⚠️ Using dummy LLM since SERVICE_ACC_KEY is not provided.")

  set_llm_cache(SQLiteCache(database_path="llm_cache.db"))
  agent = create_agent(llm, FHIR_STORE_URL)
  print("✅ LLM and Agent Initialization successful.")
except Exception as e:
  print(f"❌ LLM and Agent Initialization FAILED: {e}")
  llm = None
  agent = None


# --- Routes ---
@app.route("/")
def index():
  return render_template("index.html")


@app.route("/questions")
def get_questions():
  return jsonify(PREDEFINED_QUESTIONS)


@app.route("/run_agent")
def run_agent():
  if not agent:
    return jsonify({"error": "Agent not initialized"}), 500

  question_id = request.args.get("question_id")

  selected_question = next(
      (q for q in PREDEFINED_QUESTIONS if q["id"] == question_id), None
  )

  if not selected_question:
    return jsonify({"error": "Invalid question ID"}), 400

  composed_question = (
      f"{selected_question['question']}. Patient ID"
      f" {selected_question['patient_id']}."
  )

  def generate():
    system_prompt = "SYSTEM INSTRUCTION: think silently if needed."
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=composed_question),
    ]
    inputs = {
        "messages": messages,
        "patient_fhir_manifest": {},
        "tool_output_summary": [],
    }

    def yield_event(request, destination, event, final=False, data=""):
      return (
          "data:"
          f" {json.dumps({'request': request, 'destination': destination, 'event': event, 'final': final, 'data': data})}\n\n"
      )

    # JSON output:
    # {
    #   "request": boolean,
    #   "destination": string,
    #   "event": string,
    #   "final": boolean,
    #   "data": string
    # }

    yield yield_event(
        request=True, destination="LLM", event="Define manifest tool to LLM"
    )
    for event in agent.stream(inputs):
      if "generate_manifest_tool_call" in event:
        yield yield_event(
            request=False, destination="LLM", event="Tool call generated", data=event["generate_manifest_tool_call"]["tool_call"],
        )
        yield yield_event(
            request=True, destination="FHIR", event="Get patient resources"
        )
      elif "execute_manifest_tool_call" in event:
        yield yield_event(
            request=False,
            destination="FHIR",
            event="Patient resources received. Agent creating manifest.",
            data=event["execute_manifest_tool_call"]["patient_fhir_manifest"],
        )
      elif "identify_relevant_resource_types" in event:
        yield yield_event(
            request=True,
            destination="LLM",
            event="Identify relevant FHIR resources",
        )
        resources = event["identify_relevant_resource_types"].get(
            "relevant_resource_types", []
        )
        yield yield_event(
            request=False,
            destination="LLM",
            event="Selected FHIR resources to use",
            data=resources,
        )
      elif "announce_sdt" in event:
        node_output = event["announce_sdt"]
        resource_type = node_output.get("resource_type_to_process")
        yield yield_event(
            request=True,
            destination="LLM",
            event=f"Select data for {resource_type} resource",
            data=node_output.get("resource_manifest_codes"),
        )
      elif "select_data_to_retrieve" in event:
        node_output = event["select_data_to_retrieve"]
        resource_type = node_output.get("resource_type_processed")
        tool_call = node_output.get("tool_calls_to_execute")
        if tool_call:
          yield yield_event(
              request=False,
              destination="LLM",
              event=f"Tool call: retrieve {resource_type} resource with filter codes",
              data=tool_call,
          )

      elif "init_edr_idx" in event:
        yield yield_event(
            request=True,
            destination="FHIR",
            event="Retrieve resources from FHIR store",
        )
      elif "execute_data_retrieval" in event:
        node_output = event["execute_data_retrieval"]
        resource_type = node_output.get("resource_type_retrieved")
        yield yield_event(
            request=False,
            destination="FHIR",
            event=f"{resource_type} resource received.",
        )
      elif "announce_summarization" in event:
        node_output = event["announce_summarization"]
        resource_type = node_output.get("resource_being_summarized")
        yield yield_event(
            request=True,
            destination="LLM",
            event=f"Extract concise facts for {resource_type} resource",
        )
      elif "summarize_node" in event:
        node_output = event["summarize_node"]
        if "tool_output_summary" in node_output:
          resource_type = node_output.get("resource_type_retrieved")
          yield yield_event(
              request=False,
              destination="LLM",
              event=f"{resource_type} concise facts received.",
              data=f'...{node_output.get("tool_output_summary")[0][-200:]}'
          )
      elif "final_answer" in event:
        yield yield_event(
            request=True, destination="LLM", event="Generate final answer"
        )
        final_response = event["final_answer"]["messages"][-1].content
        final_response = final_response.removesuffix("```").removeprefix(
            "```markdown"
        )
        yield yield_event(
            request=False,
            destination="LLM",
            event="Final Answer",
            final=True,
            data=final_response,
        )

  return Response(generate(), mimetype="text/event-stream")


@app.route("/download")
def download_cache():
  try:
    return send_file("llm_cache.db", as_attachment=True)
  except Exception as e:
    return str(e), 404


@app.route("/download_fhir_cache")
def download_fhir_cache():
  try:
    return send_file("fhir_cache.db", as_attachment=True)
  except Exception as e:
    return str(e), 404


if __name__ == "__main__":
  app.run(debug=True, port=8080)
