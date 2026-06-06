#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IRIS_BIN="${IRIS_BIN:-/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry/iris}"
IRIS_INSTANCE="${IRIS_INSTANCE:-PELAGIA}"
IRIS_NAMESPACE="${IRIS_NAMESPACE:-SARAFHIR}"
FHIR_WEBAPP="${FHIR_WEBAPP:-/fhir/r4}"
SARA_WEBAPP="${SARA_WEBAPP:-/sara/api}"
IRIS_USERNAME="${IRIS_USERNAME:-_SYSTEM}"
IRIS_MGRDIR="${IRIS_MGRDIR:-/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irishealth/mgr}"
IRIS_WEB_PORT="${IRIS_WEB_PORT:-15273}"

if [[ ! -x "$IRIS_BIN" ]]; then
  echo "IRIS binary not found or not executable: $IRIS_BIN" >&2
  exit 1
fi

if [[ -z "${IRIS_PASSWORD:-}" ]]; then
  echo "Set IRIS_PASSWORD before running this script." >&2
  exit 1
fi

export IRISSYS="${IRISSYS:-/Users/alfaxad/Desktop/AI/Pelagia/research/intersystems/local-iris/irissys-registry}"
export PATH="$(dirname "$IRIS_BIN"):$PATH"
export IRIS_PASSWORD

mkdir -p "$IRIS_MGRDIR/sara-python" "$IRIS_MGRDIR/sara-demo-fhir"
cp -R "$REPO_ROOT/src/iris/python/." "$IRIS_MGRDIR/sara-python/"
cp -R "$REPO_ROOT/data/iris-fhir/." "$IRIS_MGRDIR/sara-demo-fhir/"

"$IRIS_BIN" start "$IRIS_INSTANCE" quietly || true

IRIS_SCRIPT="$(mktemp)"
{
  printf '%s\n' "$IRIS_USERNAME"
  printf '%s\n' "$IRIS_PASSWORD"
  cat <<IRIS
zn "%SYS"
write !,"Loading Sara installer",!
set sc=\$system.OBJ.Load("$REPO_ROOT/src/iris/Sara/Setup.cls","ck")
if 'sc write \$system.Status.GetErrorText(sc),! halt
if '##class(%Dictionary.CompiledClass).%ExistsId("Sara.Setup") write "Sara.Setup did not compile",! halt
write !,"Installing Sara for IRIS",!
set sc=##class(Sara.Setup).Install("$IRIS_NAMESPACE","$FHIR_WEBAPP","$SARA_WEBAPP",1,"JsonAdvSql")
if 'sc write \$system.Status.GetErrorText(sc),! halt
zn "$IRIS_NAMESPACE"
set prodStatus=##class(Ens.Director).GetProductionStatus()
if prodStatus>0 write !,"Stopping existing Sara production",!
if prodStatus>0 set sc=##class(Ens.Director).StopProduction()
if prodStatus>0 write \$system.Status.GetErrorText(sc),!
if prodStatus>0 hang 5
IRIS

  class_files=(
    "src/iris/Sara/Message/TaskRequest.cls"
    "src/iris/Sara/Message/TaskResponse.cls"
    "src/iris/Sara/Message/TraceEvent.cls"
    "src/iris/Sara/REST/TaskBusinessService.cls"
    "src/iris/Sara/REST/TaskService.cls"
    "src/iris/Sara/Interop/AgentProcess.cls"
    "src/iris/Sara/Interop/Production.cls"
  )

  for cls_file in "${class_files[@]}"; do
    cls_file="$REPO_ROOT/$cls_file"
    printf 'write !,"Loading %s",!\n' "$cls_file"
    printf 'set sc=$system.OBJ.Load("%s","ck")\n' "$cls_file"
    printf "if 'sc write \$system.Status.GetErrorText(sc),! halt\n"
  done

  cat <<IRIS
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRBaseURL","http://localhost:${IRIS_WEB_PORT}${FHIR_WEBAPP}")
if 'sc write \$system.Status.GetErrorText(sc),! halt
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRUsername","${IRIS_USERNAME}")
if 'sc write \$system.Status.GetErrorText(sc),! halt
set fhirPassword=\$system.Util.GetEnviron("IRIS_PASSWORD")
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRPassword",fhirPassword)
if 'sc write \$system.Status.GetErrorText(sc),! halt
set sc=##class(Ens.Director).StartProduction("Sara.Interop.Production")
if 'sc write \$system.Status.GetErrorText(sc),! halt
write !,"SARA_NATIVE_SETUP_OK",!
halt
IRIS
} > "$IRIS_SCRIPT"

"$IRIS_BIN" session "$IRIS_INSTANCE" < "$IRIS_SCRIPT"

rm -f "$IRIS_SCRIPT"

cat <<EOF
Sara for IRIS setup attempted.

FHIR endpoint:
  http://localhost:15273${FHIR_WEBAPP}

Sara endpoint:
  http://localhost:15273${SARA_WEBAPP}/health

Production:
  ${IRIS_NAMESPACE}: Sara.Interop.Production
EOF
