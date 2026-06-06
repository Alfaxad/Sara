"""Modal-hosted InterSystems IRIS for Health FHIR server for Sara.

This service pulls the official IRIS for Health Community container, starts the
IRIS instance inside Modal, installs the Sara ObjectScript package, loads the
demo FHIR bundle, and exposes the IRIS web server port as a public Modal URL.

Deploy:
    modal deploy src/iris/modal_iris.py

Probe the container:
    modal run src/iris/modal_iris.py
"""

import os
import shlex
import subprocess
import textwrap
import time
from pathlib import Path

import httpx
import modal
from fastapi import FastAPI, Request, Response

IRIS_IMAGE = "containers.intersystems.com/intersystems/irishealth-community:2026.1"
IRIS_PORT = 52773
IRIS_INSTANCE = "IRIS"
IRIS_NAMESPACE = "SARAFHIR"
FHIR_WEBAPP = "/fhir/r4"
SARA_WEBAPP = "/sara/api"
APP_ROOT = Path("/app")
IRIS_DATA_DIR = Path("/durable/iris")
READY_MARKER = Path("/durable/sara-iris-ready.txt")

image = (
    modal.Image.from_registry(IRIS_IMAGE, add_python="3.12")
    .entrypoint([])
    .workdir("/app")
    .pip_install(
        "fastapi[standard]>=0.115.0",
        "httpx>=0.27.0",
    )
    .add_local_dir("src/iris", remote_path="/app/src/iris", copy=True)
    .add_local_dir("data/iris-fhir", remote_path="/app/data/iris-fhir", copy=True)
)

app = modal.App("sara-iris-health")
iris_volume = modal.Volume.from_name("sara-iris-health-data", create_if_missing=True)


def _iris_data_directory_env() -> str:
    return str(IRIS_DATA_DIR.resolve())


def _run(command: list[str], *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _which(name: str) -> str:
    result = _run(["bash", "-lc", f"command -v {name}"], check=False)
    return result.stdout.strip()


def _iris_main_path() -> str:
    for candidate in ("/iris-main", _which("iris-main"), "/usr/irissys/bin/iris-main"):
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Could not locate iris-main in the IRIS container")


def _iris_bin_path() -> str:
    for candidate in (_which("iris"), "/usr/irissys/bin/iris"):
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Could not locate iris binary in the IRIS container")


def _as_irisowner(command: list[str]) -> list[str]:
    env = {
        "HOME": "/home/irisowner",
        "USER": "irisowner",
        "LOGNAME": "irisowner",
    }
    if "ISC_CPF_MERGE_FILE" in os.environ:
        env["ISC_CPF_MERGE_FILE"] = os.environ["ISC_CPF_MERGE_FILE"]
    if "ISC_DATA_DIRECTORY" in os.environ:
        env["ISC_DATA_DIRECTORY"] = os.environ["ISC_DATA_DIRECTORY"]
    exports = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    shell_command = (
        "cd /home/irisowner && "
        f"export {exports} && "
        f"exec {shlex.join(command)}"
    )
    return ["su", "-s", "/bin/sh", "irisowner", "-c", shell_command]


def _wait_for_iris(iris_bin: str, process: subprocess.Popen[str], timeout_seconds: int = 300) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(f"iris-main exited before {IRIS_INSTANCE} became ready with code {exit_code}")
        result = _run(_as_irisowner([iris_bin, "list"]), check=False)
        print(result.stdout.strip(), flush=True)
        if IRIS_INSTANCE in result.stdout and "running" in result.stdout.lower():
            probe = _run(
                _as_irisowner([iris_bin, "session", IRIS_INSTANCE]),
                input_text='write "SARA_IRIS_READY",!\nhalt\n',
                check=False,
            )
            if "SARA_IRIS_READY" in probe.stdout:
                return
            print(probe.stdout.strip(), flush=True)
        time.sleep(2)
    raise TimeoutError(f"IRIS instance {IRIS_INSTANCE} did not become ready")


def _print_startup_diagnostics() -> None:
    diagnostics = {
        "processes": "ps aux | grep -Ei 'iris|iscagent|cache' | grep -v grep || true",
        "list-root": "iris list || true",
        "qlist-root": "iris qlist || true",
        "list-irisowner": "su -s /bin/sh irisowner -c 'iris list' || true",
        "qlist-irisowner": "su -s /bin/sh irisowner -c 'iris qlist' || true",
        "ports": "ss -ltnp || true",
        "usr-messages": "tail -200 /usr/irissys/mgr/messages.log 2>/dev/null || true",
        "durable-messages": "tail -240 /durable/iris/mgr/messages.log 2>/dev/null || true",
        "owner-messages": "tail -200 /home/irisowner/irissys/mgr/messages.log 2>/dev/null || true",
        "iscagent": "tail -200 /home/irisowner/irissys/iscagent.log 2>/dev/null || true",
    }
    for name, command in diagnostics.items():
        print(f"\n--- IRIS startup diagnostic: {name} ---", flush=True)
        print(_run(["bash", "-lc", command], check=False).stdout, flush=True)


def _prepare_durable_data_dir() -> None:
    if IRIS_DATA_DIR.parent.exists():
        _run(["chown", "irisowner:irisowner", str(IRIS_DATA_DIR.parent)])
        if IRIS_DATA_DIR.exists():
            _run(["chown", "-R", "irisowner:irisowner", str(IRIS_DATA_DIR)])


def _reset_durable_data_dir() -> None:
    if READY_MARKER.exists():
        READY_MARKER.unlink()
    if IRIS_DATA_DIR.exists():
        _run(["rm", "-rf", str(IRIS_DATA_DIR)])
    iris_volume.commit()


def _manager_dir() -> Path:
    data_directory = os.environ.get("ISC_DATA_DIRECTORY")
    if data_directory:
        return Path(data_directory) / "mgr"
    return Path("/usr/irissys/mgr")


def _stage_assets() -> None:
    mgr_dir = _manager_dir()
    (mgr_dir / "sara-python").mkdir(parents=True, exist_ok=True)
    (mgr_dir / "sara-demo-fhir").mkdir(parents=True, exist_ok=True)
    _run(["bash", "-lc", f"cp -R /app/src/iris/python/. {shlex.quote(str(mgr_dir / 'sara-python'))}/"])
    _run(["bash", "-lc", f"cp -R /app/data/iris-fhir/. {shlex.quote(str(mgr_dir / 'sara-demo-fhir'))}/"])
    _run(
        [
            "bash",
            "-lc",
            "chown -R irisowner:irisowner "
            f"{shlex.quote(str(mgr_dir / 'sara-python'))} {shlex.quote(str(mgr_dir / 'sara-demo-fhir'))}",
        ]
    )


def _install_sara_package(iris_bin: str) -> None:
    class_files = [
        "src/iris/Sara/Message/TaskRequest.cls",
        "src/iris/Sara/Message/TaskResponse.cls",
        "src/iris/Sara/Message/TraceEvent.cls",
        "src/iris/Sara/REST/TaskBusinessService.cls",
        "src/iris/Sara/REST/TaskService.cls",
        "src/iris/Sara/Interop/AgentProcess.cls",
        "src/iris/Sara/Interop/Production.cls",
    ]
    load_commands = []
    for cls_file in class_files:
        full_path = APP_ROOT / cls_file
        load_commands.append(
            f'''
write !,"Loading {full_path}",!
set sc=$system.OBJ.Load("{full_path}","ck")
if 'sc write $system.Status.GetErrorText(sc),! halt
'''
        )

    iris_password = os.environ.get("IRIS_PASSWORD", "")
    install_script = f"""
zn "%SYS"
write !,"Loading Sara installer",!
set sc=$system.OBJ.Load("{APP_ROOT / 'src/iris/Sara/Setup.cls'}","ck")
if 'sc write $system.Status.GetErrorText(sc),! halt
write !,"Installing Sara for IRIS",!
set sc=##class(Sara.Setup).Install("{IRIS_NAMESPACE}","{FHIR_WEBAPP}","{SARA_WEBAPP}",1,"JsonAdvSql")
if 'sc write $system.Status.GetErrorText(sc),! halt
zn "{IRIS_NAMESPACE}"
{''.join(load_commands)}
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRBaseURL","http://localhost:{IRIS_PORT}{FHIR_WEBAPP}")
if 'sc write $system.Status.GetErrorText(sc),! halt
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRUsername","_SYSTEM")
if 'sc write $system.Status.GetErrorText(sc),! halt
set sc=##class(Ens.Director).SetHostSettingValue("Sara.Interop.AgentProcess","FHIRPassword","{iris_password}")
if 'sc write $system.Status.GetErrorText(sc),! halt
set sc=##class(Ens.Director).StartProduction("Sara.Interop.Production")
if 'sc write $system.Status.GetErrorText(sc),! halt
write !,"SARA_MODAL_IRIS_SETUP_OK",!
halt
"""
    result = _run(
        _as_irisowner([iris_bin, "session", IRIS_INSTANCE]),
        input_text=textwrap.dedent(install_script),
        check=False,
    )
    if "SARA_MODAL_IRIS_SETUP_OK" not in result.stdout:
        already_running = "ErrProductionAlreadyRunning" in result.stdout and "Sara.Interop.Production" in result.stdout
        if not already_running:
            raise RuntimeError(f"Sara IRIS install failed; output tail:\n{result.stdout[-12000:]}")
        print("Sara.Interop.Production is already running; accepting idempotent setup", flush=True)


def _start_iris() -> subprocess.Popen[str]:
    password = os.environ.get("IRIS_PASSWORD", "SaraModalLocal123")
    password_file = Path("/home/irisowner/.sara-iris-password")
    password_file.write_text(password)
    _run(["chown", "irisowner:irisowner", str(password_file)])
    password_file.chmod(0o600)

    iris_main = _iris_main_path()
    os.environ["ISC_CPF_MERGE_FILE"] = "/app/src/iris/modal-merge.cpf"
    if IRIS_DATA_DIR.parent.exists():
        _prepare_durable_data_dir()
        os.environ["ISC_DATA_DIRECTORY"] = _iris_data_directory_env()
    print(f"Starting IRIS with {iris_main} as irisowner", flush=True)
    return subprocess.Popen(
        _as_irisowner([iris_main, "--password-file", str(password_file), "--check-caps", "false"]),
        text=True,
    )


def _stop_iris(iris_bin: str, process: subprocess.Popen[str]) -> None:
    _run(_as_irisowner([iris_bin, "stop", IRIS_INSTANCE, "quietly"]), check=False)
    try:
        process.wait(timeout=120)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()


def _start_iris_direct(iris_bin: str) -> str:
    merge = _run(_as_irisowner([iris_bin, "merge", IRIS_INSTANCE, "/app/src/iris/modal-merge.cpf"]), check=False)
    start = _run(_as_irisowner([iris_bin, "start", IRIS_INSTANCE, "quietly"]), check=False)
    return f"--- merge ---\n{merge.stdout}\n--- start ---\n{start.stdout}"


@app.function(
    image=image,
    cpu=2.0,
    memory=16384,
    timeout=30 * 60,
)
def inspect_image() -> dict[str, str]:
    """Return basic facts about the official IRIS image in Modal."""
    commands = {
        "id": "id",
        "working-directory": "pwd",
        "iris": "command -v iris || true",
        "iris-main": "command -v iris-main || true; ls -l /iris-main 2>/dev/null || true",
        "iris-main-strings": "strings /iris-main 2>/dev/null | sed -n '1,220p' || true",
        "users": "grep -E '^(irisowner|root):' /etc/passwd; grep -E '^(irisowner|root):' /etc/group",
        "registry-files": "find / -maxdepth 4 \\( -name 'iris.reg' -o -name 'iris.cpf' \\) 2>/dev/null | sort | xargs -r ls -la",
        "registry-content": "find / -maxdepth 4 -name 'iris.reg' 2>/dev/null | sort | xargs -r strings | sed -n '1,120p'",
        "ownership": "ls -ld /usr/irissys /usr/irissys/mgr /home/irisowner /home/irisowner/irissys 2>/dev/null || true",
        "irissys": "ls -la /usr/irissys/bin 2>/dev/null | sed -n '1,40p'",
        "ports": "ss -ltnp 2>/dev/null || true",
    }
    return {name: _run(["bash", "-lc", command], check=False).stdout for name, command in commands.items()}


@app.function(
    image=image,
    cpu=2.0,
    memory=16384,
    timeout=60 * 60,
    scaledown_window=60 * 60,
    max_containers=1,
    volumes={"/durable": iris_volume},
    secrets=[modal.Secret.from_name("sara-iris-password")],
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def serve():
    print("Sara Modal IRIS service starting", flush=True)
    process = _start_iris()
    iris_bin = _iris_bin_path()
    print(f"Waiting for {IRIS_INSTANCE} via {iris_bin}", flush=True)
    try:
        _wait_for_iris(iris_bin, process)
    except Exception:
        _print_startup_diagnostics()
        raise
    if READY_MARKER.exists():
        print("Sara Modal IRIS setup marker found; refreshing Sara assets", flush=True)
        _stage_assets()
        print("Sara Modal IRIS assets refreshed; serving IRIS web port", flush=True)
    else:
        print("IRIS is running but Sara setup marker is missing; staging Sara assets", flush=True)
        _stage_assets()
        print("Installing Sara package into IRIS", flush=True)
        _install_sara_package(iris_bin)
        READY_MARKER.write_text(f"ready {time.time()}\n")
        iris_volume.commit()
        print("Sara Modal IRIS setup completed; serving IRIS web port", flush=True)

    fastapi_app = FastAPI(title="Sara IRIS Health Proxy")

    async def proxy_to_iris(path: str, request: Request) -> Response:
        target = f"http://127.0.0.1:{IRIS_PORT}/{path}"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "content-length"}
        }
        body = await request.body()
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
            upstream = await client.request(request.method, target, headers=headers, content=body)
        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in {"content-encoding", "transfer-encoding", "connection"}
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
            media_type=upstream.headers.get("content-type"),
        )

    @fastapi_app.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def proxy_root(request: Request):
        return await proxy_to_iris("", request)

    @fastapi_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def proxy_path(path: str, request: Request):
        return await proxy_to_iris(path, request)

    @fastapi_app.on_event("shutdown")
    async def shutdown_iris():
        _stop_iris(iris_bin, process)
        iris_volume.commit()

    return fastapi_app


@app.function(
    image=image,
    cpu=2.0,
    memory=16384,
    timeout=60 * 60,
    volumes={"/durable": iris_volume},
    secrets=[modal.Secret.from_name("sara-iris-password")],
)
def initialize(force: bool = False, reset: bool = False) -> dict[str, str]:
    """Initialize the persisted IRIS data volume before serving web traffic."""
    if reset:
        _reset_durable_data_dir()

    if READY_MARKER.exists() and not force:
        return {"status": "already-ready", "marker": READY_MARKER.read_text().strip()}

    print("Initializing Sara IRIS durable volume", flush=True)
    process = _start_iris()
    iris_bin = _iris_bin_path()
    try:
        _wait_for_iris(iris_bin, process)
        _stage_assets()
        _install_sara_package(iris_bin)
        READY_MARKER.write_text(f"ready {time.time()}\n")
        iris_volume.commit()
        return {"status": "initialized", "marker": READY_MARKER.read_text().strip()}
    except Exception:
        _print_startup_diagnostics()
        raise
    finally:
        _stop_iris(iris_bin, process)
        iris_volume.commit()


@app.function(
    image=image,
    cpu=2.0,
    memory=16384,
    timeout=15 * 60,
    volumes={"/durable": iris_volume},
    secrets=[modal.Secret.from_name("sara-iris-password")],
)
def diagnose_volume(start_direct: bool = False) -> dict[str, str]:
    """Inspect the persisted IRIS data volume and optionally try direct startup."""
    os.environ["ISC_CPF_MERGE_FILE"] = "/app/src/iris/modal-merge.cpf"
    os.environ["ISC_DATA_DIRECTORY"] = _iris_data_directory_env()
    _prepare_durable_data_dir()
    iris_bin = _iris_bin_path()

    output: dict[str, str] = {}
    output["durable-files"] = _run(
        ["bash", "-lc", "find /durable -maxdepth 3 | sort | sed -n '1,120p'"],
        check=False,
    ).stdout
    output["iris-list"] = _run(_as_irisowner([iris_bin, "list"]), check=False).stdout
    output["iris-qlist"] = _run(_as_irisowner([iris_bin, "qlist"]), check=False).stdout
    output["cpf-settings"] = _run(
        ["bash", "-lc", "grep -Ei '^(globals|gmheap|routines|webserver|superserver)' /durable/iris/iris.cpf 2>/dev/null || true"],
        check=False,
    ).stdout
    output["durable-messages"] = _run(
        ["bash", "-lc", "tail -80 /durable/iris/mgr/messages.log 2>/dev/null || true"],
        check=False,
    ).stdout

    if start_direct:
        output["direct-start"] = _start_iris_direct(iris_bin)
        output["iris-list-after-start"] = _run(_as_irisowner([iris_bin, "list"]), check=False).stdout
        output["session-probe"] = _run(
            _as_irisowner([iris_bin, "session", IRIS_INSTANCE]),
            input_text='write "SARA_DIRECT_READY",!\nhalt\n',
            check=False,
        ).stdout
        output["ports-after-start"] = _run(["bash", "-lc", "ss -ltnp || true"], check=False).stdout
        output["durable-messages-after-start"] = _run(
            ["bash", "-lc", "tail -100 /durable/iris/mgr/messages.log 2>/dev/null || true"],
            check=False,
        ).stdout
        _run(_as_irisowner([iris_bin, "stop", IRIS_INSTANCE, "quietly"]), check=False)
        iris_volume.commit()

    return output


@app.local_entrypoint()
def main(
    init: bool = True,
    inspect: bool = False,
    force: bool = False,
    reset: bool = False,
    diagnose: bool = False,
    start_direct: bool = False,
):
    import json

    if inspect:
        print(json.dumps(inspect_image.remote(), indent=2))
    if diagnose:
        print(json.dumps(diagnose_volume.remote(start_direct=start_direct), indent=2))
    if init:
        print(json.dumps(initialize.remote(force=force, reset=reset), indent=2))
