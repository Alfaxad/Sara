import json
from typing import Optional
from urllib.parse import quote
import hashlib
import sqlite3

from google.auth import default as get_auth_default
import google.auth.transport.requests as google_auth_requests
from langchain_core.tools import tool
import requests

fhir_resource_types = [
    "Encounter",
    "Practitioner",
    "Condition",
    "Observation",
    "AllergyIntolerance",
    "FamilyMemberHistory",
    "MedicationRequest",
    "MedicationStatement",
    "MedicationAdministration",
    "DiagnosticReport",
    "Procedure",
    "ServiceRequest",
]


SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-healthcare",
]


FHIR_CACHE_DB = "fhir_cache.db"

def _init_fhir_cache():
  conn = sqlite3.connect(FHIR_CACHE_DB)
  cursor = conn.cursor()
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS fhir_cache (
      key TEXT PRIMARY KEY,
      value TEXT
    )
  """)
  conn.commit()
  conn.close()

_init_fhir_cache()


def _get_fhir_resource(resource_path: str, fhir_store_url: str) -> dict:
  """Helper function to make an authenticated GET request to the FHIR store, with pagination and compaction."""
  cache_key = hashlib.md5(f"{resource_path}:{fhir_store_url}".encode()).hexdigest()
  conn = sqlite3.connect(FHIR_CACHE_DB)
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT value FROM fhir_cache WHERE key = ?", (cache_key,))
    result = cursor.fetchone()
    if result:
      print(f"...[Tool] Cache hit for: {fhir_store_url}/{resource_path}")
      return json.loads(result[0])
  except Exception as e:
    print(f"...[Tool] Cache read error: {str(e)}")
    # If cache read fails, we proceed without cache

  try:
    credentials, _ = get_auth_default(scopes=SCOPES)
    request = google_auth_requests.Request()
    credentials.refresh(request)
    headers = {"Authorization": f"Bearer {credentials.token}"}

    all_entries = []
    url = f"{fhir_store_url}/{resource_path}"

    while url:
      print(f"...[Tool] Making request to: {url}")
      response = requests.get(url, headers=headers)
      response.raise_for_status()
      current_page = response.json()

      if "entry" in current_page:
        all_entries.extend(current_page["entry"])

      url = None  # Reset url for each iteration
      for link in current_page.get("link", []):
        if link.get("relation") == "next":
          url = link.get("url")
          break

    # Reconstruct the bundle with all entries
    data = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(all_entries),
        "entry": all_entries,
    }

    def clean(obj):
      # Remove .resource.meta (timestamps/versions) from all objects
      if isinstance(obj, list):
        return [clean(i) for i in obj]
      if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items() if k != "meta"}
      return (
          obj.split("/fhir/")[-1]
          if isinstance(obj, str) and "/fhir/" in obj
          else obj
      )

    # [OPTIONAL] Strip technical metadata and shorten URLs
    for e in all_entries:
      e.pop("fullUrl", None)
      e.pop("search", None)
      if "resource" in e:
        e["resource"] = clean(e["resource"])

    try:
      cursor.execute(
          "INSERT INTO fhir_cache (key, value) VALUES (?, ?)",
          (cache_key, json.dumps(data)),
      )
      conn.commit()
    except Exception as e:
      print(f"...[Tool] Cache write error: {str(e)}")
    return data
  except Exception as e:
    print(f"...[Tool] Error: {str(e)}")
    return {"error": f"An error occurred: {str(e)}"}
  finally:
    conn.close()


@tool
def get_patient_fhir_resource(
    patient_id: str,
    fhir_resource: str,
    fhir_store_url: str,
    filter_code: Optional[str] = None,
) -> str:
  """Gets a list of FHIR resources for a single patient.

  patient_id: The ID of the patient. fhir_resource: The FHIR resource type to
  retrieve (Observation, Condition, MedicationRequest, etc.) fhir_store_url: The
  URL of the FHIR store. filter_code: A comma seperated list of code filter to
  apply to the resource (34117-2, 171207006, 82667-7, 8867-4, etc)
  """
  resource_path = f"{fhir_resource}?patient=Patient/{patient_id}"
  if filter_code:
    resource_path += f"&code={quote(filter_code.replace(' ', ''))}"
  if "Medication" in fhir_resource:
    resource_path += f"&_include={fhir_resource}:medication"

  content = _get_fhir_resource(resource_path, fhir_store_url)

  # If the initial call with code:text returns no results, try with category:text
  if content.get("total", 0) == 0 and filter_code:
    print(
        "...[Tool] No results found with 'code:text'. Retrying with"
        " 'category:text'..."
    )
    resource_path = f"{fhir_resource}?patient=Patient/{patient_id}&category={quote(filter_code)}"
    content = _get_fhir_resource(resource_path, fhir_store_url)

  print(
      f"...[Tool] Returning {len(content.get('entry', []))} results for"
      f" {fhir_resource}"
  )
  return json.dumps(content)


@tool
def get_patient_data_manifest(patient_id: str, fhir_store_url: str) -> str:
  """Gets a manifest of all available FHIR resources and their codes for a patient by

  querying the patient's entire record. Use this tool first to discover what
  data is available.
  """
  manifest = {}

  for resource_type in fhir_resource_types:
    resource_path = f"{resource_type}?patient=Patient/{patient_id}"
    print(
        f"...[Tool] Discovering all available {resource_type} resources for"
        f" patient: {patient_id}"
    )
    resources_json = _get_fhir_resource(resource_path, fhir_store_url)

    if isinstance(resources_json, dict) and resources_json.get("total", 0) > 0:
      for entry in resources_json.get("entry", []):
        resource = entry.get("resource", {})
        if resource_type not in manifest:
          manifest[resource_type] = []

        if "code" in resource and "coding" in resource["code"]:
          for code in resource.get("code").get("coding", []):
            manifest[resource_type].append(
                f'{code.get("display", "")}={code.get("code", "")}'
            )
    else:
      print(
          f"...[Tool] No {resource_type} resources found for patient:"
          f" {patient_id}"
      )

  return json.dumps(manifest)
