from __future__ import annotations

import hashlib
import http.client
import json
import os
import py_compile
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator, RefResolver


TRACK_RESOURCES = {
    "posting": {"ACCTFILE", "DALYTRAN", "TCATBALF", "TRANFILE", "XREFFILE"},
    "interest": {"ACCTFILE", "DISCGRP", "TCATBALF", "XREFFILE", "XREFFILE.1", "PARMFILE"},
    "reporting": {"CARDXREF", "DATEPARM", "TRANCATG", "TRANFILE", "TRANTYPE"},
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def descriptor_sha256(fixture: dict[str, Any]) -> str:
    canonical = {k: v for k, v in fixture.items() if k != "contentSha256"}
    return sha256_bytes(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode())


def copy_current_fixture_package(source: Path, dest: Path) -> Path:
    source = Path(source).resolve()
    dest = Path(dest).resolve()
    if not (source / "manifest.json").is_file():
        raise FileNotFoundError(f"fixture package manifest not found: {source}")
    if dest.exists():
        raise FileExistsError(f"destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, symlinks=False)
    for path in dest.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"copied fixture package contains symlink: {path}")
    return dest


def build_fixture_registry_from_copy(package: Path, registry_path: Path) -> Path:
    package = Path(package).resolve()
    registry_path = Path(registry_path).resolve()
    fixtures = []
    for track, required in TRACK_RESOURCES.items():
        track_dir = package / track
        if not track_dir.is_dir():
            raise FileNotFoundError(f"missing track fixture directory: {track_dir}")
        files: dict[str, str] = {}
        pins: dict[str, dict[str, Any]] = {}
        for dd in sorted(required):
            p = track_dir / dd
            if not p.is_file():
                raise FileNotFoundError(f"missing resource {track}/{dd}")
            rel = p.relative_to(registry_path.parent).as_posix() if p.is_relative_to(registry_path.parent) else p.relative_to(package.parent).as_posix()
            if p.is_relative_to(registry_path.parent):
                rel = p.relative_to(registry_path.parent).as_posix()
            else:
                # registry is normally written next to the copied package; this is a hard failure otherwise.
                raise ValueError("registry_path must be in an ancestor of copied package")
            files[dd] = rel
            data = p.read_bytes()
            pins[dd] = {"sha256": sha256_bytes(data), "bytes": len(data)}
        fixture = {
            "fixtureId": f"{track}.copied-current-technical-smoke",
            "track": track,
            "materializer": {"kind": "local_file_package", "files": files, "filePins": pins},
            "provenance": {"source": str(package), "copiedCurrent": True, "officialFixture": False},
            "exposure": {"label": "technical-only", "notOracle": True, "notExtractionInput": True, "notPublicRequest": True},
            "reset": {"default": "fresh_dir_per_run", "statefulSequence": "not_used"},
        }
        fixture["contentSha256"] = descriptor_sha256(fixture)
        fixtures.append(fixture)
    registry = {"kind": "p3-local-technical-fixture-selection", "status": "isolated_copy_technical_only", "fixtures": fixtures}
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    return registry_path


@dataclass
class CheckResult:
    ok: bool
    classification: str
    detail: dict[str, Any]


class ContractChecker:
    def __init__(self, openapi_path: Path):
        self.path = Path(openapi_path)
        self.spec = yaml.safe_load(self.path.read_text())
        self.resolver = RefResolver.from_schema(self.spec)

    def _operation(self, method: str, path: str) -> dict[str, Any] | None:
        item = (self.spec.get("paths") or {}).get(path)
        if not isinstance(item, dict):
            return None
        op = item.get(method.lower())
        return op if isinstance(op, dict) else None

    def _resolve(self, obj: dict[str, Any]) -> dict[str, Any]:
        if "$ref" not in obj:
            return obj
        cur: Any = self.spec
        for part in obj["$ref"].removeprefix("#/").split("/"):
            cur = cur[part]
        return cur

    def check(self, method: str, path: str, status: int | None, content_type: str | None, body: bytes) -> CheckResult:
        if status is None:
            return CheckResult(False, "infra_transport", {"reason": "no HTTP status"})
        op = self._operation(method, path)
        if op is None:
            return CheckResult(False, "route_violation", {"method": method, "path": path})
        responses = op.get("responses") or {}
        status_key = str(status)
        if status_key not in responses:
            return CheckResult(False, "status_violation", {"status": status, "documented": sorted(responses)})
        if not (content_type or "").lower().split(";")[0].strip() == "application/json":
            return CheckResult(False, "content_type_violation", {"content_type": content_type})
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception as exc:
            return CheckResult(False, "json_violation", {"error": repr(exc)})
        resp = self._resolve(responses[status_key])
        schema = (((resp.get("content") or {}).get("application/json") or {}).get("schema"))
        if schema is not None:
            errors = [e.message for e in Draft202012Validator(schema, resolver=self.resolver).iter_errors(payload)]
            if errors:
                return CheckResult(False, "schema_violation", {"status": status, "errors": errors})
        if status == 500:
            return CheckResult(True, "documented_500_schema_valid", {"status": status})
        return CheckResult(True, "schema_valid", {"status": status})


@dataclass
class HarnessCase:
    arm: str
    contract_id: str
    track: str
    method: str
    path: str
    body: dict[str, Any]
    openapi_path: Path


class PosixSpawnServer:
    def __init__(self, argv_template: list[str], cwd: Path, env: dict[str, str] | None = None, startup_timeout: float = 60.0):
        self.argv_template = list(argv_template)
        self.cwd = Path(cwd)
        self.env = dict(env or {})
        self.startup_timeout = startup_timeout
        self.pid: int | None = None
        self.port_file: Path | None = None
        self.stdout_path: Path | None = None
        self.stderr_path: Path | None = None
        self.spawn_method = "not_started"
        self.quiet_tree_proven = False

    def start(self, workdir: Path) -> str:
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        self.port_file = workdir / "server.port"
        self.stdout_path = workdir / "server.stdout"
        self.stderr_path = workdir / "server.stderr"
        argv = [part.format(port_file=str(self.port_file), workdir=str(workdir)) for part in self.argv_template]
        if len(argv) >= 2 and Path(argv[1]).suffix == ".py" and "python" in Path(argv[0]).name:
            try:
                py_compile.compile(argv[1], doraise=True)
            except py_compile.PyCompileError as exc:
                message = f"py_compile failed before server startup: {exc}\n"
                self.stderr_path.write_text(message)
                raise RuntimeError(f"server entrypoint py_compile failed; stderr={message}") from exc
        env = os.environ.copy(); env.update({k: str(v) for k, v in self.env.items()}); env["PWD"] = str(self.cwd)
        out_fd = os.open(self.stdout_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
        err_fd = os.open(self.stderr_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
        try:
            if hasattr(os, "posix_spawn"):
                # /bin/sh performs the cwd change, then execs the requested Python command.
                import shlex
                shell_cmd = "cd " + shlex.quote(str(self.cwd)) + " && exec " + " ".join(shlex.quote(x) for x in argv)
                file_actions = [(os.POSIX_SPAWN_DUP2, out_fd, 1), (os.POSIX_SPAWN_DUP2, err_fd, 2)]
                kwargs = {"file_actions": file_actions}
                try:
                    self.pid = os.posix_spawn("/bin/sh", ["/bin/sh", "-c", shell_cmd], env, setsid=True, **kwargs)  # type: ignore[arg-type]
                    self.spawn_method = "posix_spawn_setsidshell_exec"
                except TypeError:
                    self.pid = os.posix_spawn("/bin/sh", ["/bin/sh", "-c", shell_cmd], env, **kwargs)  # type: ignore[arg-type]
                    self.spawn_method = "posix_spawn_shell_exec"
            else:
                proc = subprocess.Popen(argv, cwd=self.cwd, env=env, stdout=out_fd, stderr=err_fd, close_fds=True, start_new_session=True)
                self.pid = proc.pid
                self.spawn_method = "subprocess_exec_start_new_session"
        finally:
            os.close(out_fd); os.close(err_fd)
        deadline = time.time() + self.startup_timeout
        while time.time() < deadline:
            if self.port_file.exists() and self.port_file.read_text().strip():
                return f"http://127.0.0.1:{int(self.port_file.read_text().strip())}"
            if self.pid and not pid_alive(self.pid):
                raise RuntimeError(f"server exited before writing port; stderr={self.stderr_path.read_text() if self.stderr_path else ''}")
            time.sleep(0.05)
        raise TimeoutError("server did not write port file")

    def stop(self) -> bool:
        if not self.pid:
            self.quiet_tree_proven = True
            return True
        pid = self.pid
        try:
            os.killpg(pid, signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.time() + 5
        while time.time() < deadline and pid_alive(pid):
            try:
                waited, _status = os.waitpid(pid, os.WNOHANG)
                if waited == pid:
                    break
            except ChildProcessError:
                break
            time.sleep(0.05)
        if pid_alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except Exception:
                try: os.kill(pid, signal.SIGKILL)
                except ProcessLookupError: pass
            try: os.waitpid(pid, 0)
            except ChildProcessError: pass
        self.quiet_tree_proven = not pid_alive(pid) and not descendants_alive(pid)
        return self.quiet_tree_proven


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def descendants_alive(pid: int) -> bool:
    proc = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,comm="], text=True, capture_output=True, timeout=10)
    children: dict[int, list[int]] = {}
    for line in proc.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) >= 2:
            try: child, parent = int(parts[0]), int(parts[1])
            except ValueError: continue
            children.setdefault(parent, []).append(child)
    stack = list(children.get(pid, []))
    while stack:
        child = stack.pop()
        if pid_alive(child):
            return True
        stack.extend(children.get(child, []))
    return False


def send_json(base_url: str, method: str, path: str, body: dict[str, Any], timeout: float = 180.0) -> tuple[int, str | None, bytes]:
    parsed = urlparse(base_url)
    conn = http.client.HTTPConnection(parsed.hostname or "127.0.0.1", parsed.port or 80, timeout=timeout)
    data = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
    try:
        conn.request(method.upper(), path, body=data, headers={"content-type": "application/json", "content-length": str(len(data))})
        resp = conn.getresponse()
        raw = resp.read()
        return resp.status, resp.getheader("content-type"), raw
    finally:
        conn.close()


# Unified preflight protocol compatibility: replay_suite calls start(workdir) and stop();
# quiet() is retained for explicit evidence and tests without exposing setup/reset controls.
def _quiet(self) -> bool:
    return bool(getattr(self, "quiet_tree_proven", False))
PosixSpawnServer.quiet = _quiet  # type: ignore[attr-defined]

_original_start = PosixSpawnServer.start
_original_stop = PosixSpawnServer.stop

def _start_with_lifecycle(self, workdir):
    base = _original_start(self, workdir)
    self.last_lifecycle = {"pid": self.pid, "started": True, "spawn_method": self.spawn_method, "workdir": str(workdir)}
    return base

def _stop_with_lifecycle(self):
    quiet = _original_stop(self)
    previous = getattr(self, "last_lifecycle", {}) or {}
    self.last_lifecycle = {**previous, "pid": self.pid, "reaped": quiet, "quiet_proven": quiet, "quiet_tree_proven": quiet, "spawn_method": self.spawn_method}
    return quiet

PosixSpawnServer.start = _start_with_lifecycle  # type: ignore[method-assign]
PosixSpawnServer.stop = _stop_with_lifecycle  # type: ignore[method-assign]
