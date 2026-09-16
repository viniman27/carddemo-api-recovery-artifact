from __future__ import annotations

import base64
import copy
import hashlib
import http.client
import json
import shutil
import socket
import threading
from dataclasses import dataclass, field
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import urlparse


class VerificationError(Exception):
    pass


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_obj(data: Any) -> str:
    return _sha256_bytes(_canonical_json(data))


@dataclass(frozen=True)
class Expectation:
    expectation_id: str
    checks: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"expectation_id": self.expectation_id, "checks": self.checks}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expectation":
        return cls(str(data["expectation_id"]), dict(data.get("checks", {})))

    def hash(self) -> str:
        return _hash_obj(self.to_dict())


@dataclass(frozen=True)
class HttpRequestSpec:
    method: str
    path: str
    headers: Tuple[Tuple[str, str], ...] = ()
    body_kind: str = "absent"  # absent, bytes, json
    body_b64: Optional[str] = None

    def __post_init__(self) -> None:
        method = self.method.upper()
        object.__setattr__(self, "method", method)
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("unsupported method")
        if not self.path.startswith("/"):
            raise ValueError("path must be absolute")
        if self.body_kind not in {"absent", "bytes", "json"}:
            raise ValueError("body_kind must be absent, bytes or json")
        if self.body_kind == "absent" and self.body_b64 is not None:
            raise ValueError("absent body must not carry bytes")
        if self.body_kind != "absent" and self.body_b64 is None:
            raise ValueError("present body must carry base64 bytes")

    def body_bytes_or_none(self) -> Optional[bytes]:
        if self.body_kind == "absent":
            return None
        return base64.b64decode(self.body_b64 or "", validate=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "headers": [list(item) for item in self.headers],
            "body_kind": self.body_kind,
            "body_b64": self.body_b64,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HttpRequestSpec":
        return cls(
            str(data["method"]),
            str(data["path"]),
            tuple((str(k), str(v)) for k, v in data.get("headers", [])),
            str(data.get("body_kind", "absent")),
            data.get("body_b64"),
        )

    def stimulus_key(self) -> str:
        return _hash_obj(self.to_dict())


@dataclass
class Case:
    case_id: str
    suite_id: str
    origin: str
    request: HttpRequestSpec
    resource_package_id: str
    expectation: Expectation
    timeout_seconds: float = 5.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    sequence: Tuple[str, ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.provenance:
            self.provenance = (f"{self.suite_id}:{self.case_id}",)

    def stimulus_identity(self) -> str:
        return _hash_obj({
            "request": self.request.to_dict(),
            "resource_package_id": self.resource_package_id,
            "parameters": self.parameters,
            "sequence": list(self.sequence),
        })

    def identity_key(self) -> str:
        return _hash_obj({"stimulus": self.stimulus_identity(), "expectation_hash": self.expectation.hash()})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "suite_id": self.suite_id,
            "origin": self.origin,
            "request": self.request.to_dict(),
            "resource_package_id": self.resource_package_id,
            "expectation": self.expectation.to_dict(),
            "timeout_seconds": self.timeout_seconds,
            "parameters": self.parameters,
            "sequence": list(self.sequence),
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Case":
        return cls(
            str(data["case_id"]),
            str(data["suite_id"]),
            str(data.get("origin", data["suite_id"])),
            HttpRequestSpec.from_dict(data["request"]),
            str(data["resource_package_id"]),
            Expectation.from_dict(data["expectation"]),
            float(data.get("timeout_seconds", 5.0)),
            dict(data.get("parameters", {})),
            tuple(str(x) for x in data.get("sequence", [])),
            tuple(str(x) for x in data.get("provenance", [])),
        )


@dataclass(frozen=True)
class ResourcePin:
    sha256: str
    size: int

    def to_dict(self) -> Dict[str, Any]:
        return {"sha256": self.sha256, "size": self.size}


@dataclass
class LocalResourcePackage:
    package_id: str
    source_dir: Path
    pins: Dict[str, ResourcePin]

    @classmethod
    def from_directory(cls, package_id: str, source_dir: Path) -> "LocalResourcePackage":
        source_dir = Path(source_dir).resolve()
        if not source_dir.is_dir():
            raise VerificationError("resource source is not a directory")
        for path in source_dir.rglob("*"):
            if path.is_symlink():
                raise VerificationError(f"resource package contains symlink: {path.relative_to(source_dir)}")
        pins: Dict[str, ResourcePin] = {}
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            rel = path.relative_to(source_dir).as_posix()
            data = path.read_bytes()
            pins[rel] = ResourcePin(_sha256_bytes(data), len(data))
        return cls(package_id, source_dir, pins)

    def pin_dict(self) -> Dict[str, Dict[str, Any]]:
        return {name: pin.to_dict() for name, pin in sorted(self.pins.items())}

    def copy_fresh_to(self, target_dir: Path) -> Dict[str, Dict[str, Any]]:
        target_dir = Path(target_dir)
        if target_dir.exists():
            raise VerificationError("fresh target already exists")
        parent = target_dir.parent.resolve()
        target_resolved_parent = target_dir.resolve().parent if target_dir.exists() else parent
        if target_resolved_parent != parent:
            raise VerificationError("fresh target containment mismatch")
        shutil.copytree(str(self.source_dir), str(target_dir), symlinks=False)
        before = hash_directory(target_dir)
        expected = self.pin_dict()
        if before != expected:
            raise VerificationError("resource pin mismatch after fresh copy")
        return before


@dataclass
class Suite:
    suite_id: str
    cases: List[Case]
    resources: Dict[str, LocalResourcePackage] = field(default_factory=dict)

    def to_dict(self, include_resources: bool = False) -> Dict[str, Any]:
        data = {"suite_id": self.suite_id, "cases": [case.to_dict() for case in self.cases]}
        if include_resources and self.resources:
            data["resources"] = {pkg_id: pkg.pin_dict() for pkg_id, pkg in sorted(self.resources.items())}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Suite":
        return cls(str(data["suite_id"]), [Case.from_dict(item) for item in data.get("cases", [])])


@dataclass
class ReplayResult:
    totals: Dict[str, int]
    receipts: List[Dict[str, Any]]
    applications: List[Dict[str, Any]]
    output_dir: Path


class PerApplicationHttpTarget:
    """Loopback HTTP target with explicit per-application process/server lifecycle.

    The handler class receives the fresh application workdir via its class attribute
    ``workdir`` before the HTTPServer is started. ``stop`` shuts down, joins and
    closes the server, returning whether quietness was proven.
    """

    controlled_lifecycle = True

    def __init__(self, handler_cls: type, host: str = "127.0.0.1"):
        self.handler_cls = handler_cls
        self.host = host
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, workdir: Path) -> str:
        if self._server is not None:
            raise VerificationError("target already started")
        setattr(self.handler_cls, "workdir", str(workdir))
        self._server = HTTPServer((self.host, 0), self.handler_cls)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://{self.host}:{self._server.server_port}"

    def stop(self) -> bool:
        if self._server is None or self._thread is None:
            return True
        self._server.shutdown()
        self._thread.join(timeout=2)
        quiet = not self._thread.is_alive()
        self._server.server_close()
        self._server = None
        self._thread = None
        return quiet


class UnionBuilder:
    def build(self, suites: Iterable[Suite]) -> Tuple[Suite, List[Dict[str, Any]]]:
        ordered_suites = list(suites)
        suite_rank = {"T1": 0, "T2": 1, "T3": 2}
        ordered_suites.sort(key=lambda s: suite_rank.get(s.suite_id, 99))
        cases: List[Case] = []
        by_identity: Dict[str, int] = {}
        stimulus_to_expectations: Dict[str, set] = {}
        ledger: List[Dict[str, Any]] = []
        for suite in ordered_suites:
            for source in suite.cases:
                identity = source.identity_key()
                stimulus = source.stimulus_identity()
                expectation_hash = source.expectation.hash()
                if identity in by_identity:
                    dest = cases[by_identity[identity]]
                    dest.provenance = tuple(list(dest.provenance) + [f"{source.suite_id}:{source.case_id}"])
                    ledger.append({"source": f"{source.suite_id}:{source.case_id}", "action": "duplicate_merged", "destination": dest.case_id})
                    continue
                action = "kept"
                if stimulus in stimulus_to_expectations and expectation_hash not in stimulus_to_expectations[stimulus]:
                    action = "kept_distinct_expectation"
                stimulus_to_expectations.setdefault(stimulus, set()).add(expectation_hash)
                new_case = copy.deepcopy(source)
                new_case.case_id = f"T4-{len(cases)+1:04d}"
                new_case.suite_id = "T4"
                new_case.origin = "T4-union"
                new_case.provenance = (f"{source.suite_id}:{source.case_id}",)
                cases.append(new_case)
                by_identity[identity] = len(cases) - 1
                ledger.append({"source": f"{source.suite_id}:{source.case_id}", "action": action, "destination": new_case.case_id})
        return Suite("T4", cases), ledger


def freeze_suite(suite: Suite, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = suite.to_dict(include_resources=True)
    body["suite_freeze_sha256"] = _hash_obj(body)
    path.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_frozen_suite(path: Path) -> Suite:
    data = json.loads(path.read_text(encoding="utf-8"))
    recorded = data.pop("suite_freeze_sha256", None)
    actual = _hash_obj(data)
    if recorded != actual:
        raise VerificationError("suite freeze hash mismatch")
    return Suite.from_dict(data)


def hash_directory(directory: Path) -> Dict[str, Dict[str, Any]]:
    directory = Path(directory)
    result: Dict[str, Dict[str, Any]] = {}
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        if path.is_symlink():
            raise VerificationError(f"refusing to hash symlink: {path}")
        rel = path.relative_to(directory).as_posix()
        data = path.read_bytes()
        result[rel] = {"sha256": _sha256_bytes(data), "size": len(data)}
    return result


def _send_once(base_url: str, req: HttpRequestSpec, timeout_seconds: float) -> Dict[str, Any]:
    parsed = urlparse(base_url)
    if parsed.scheme != "http":
        raise VerificationError("only http loopback synthetic targets are supported")
    host = parsed.hostname or "127.0.0.1"
    if host not in {"127.0.0.1", "localhost"}:
        raise VerificationError("only loopback synthetic targets are supported")
    port = parsed.port or 80
    body = req.body_bytes_or_none()
    conn = http.client.HTTPConnection(host, port, timeout=timeout_seconds)
    try:
        conn.putrequest(req.method, req.path, skip_accept_encoding=True)
        has_content_length = any(k.lower() == "content-length" for k, _ in req.headers)
        for key, value in req.headers:
            conn.putheader(key, value)
        if body is not None and not has_content_length:
            conn.putheader("Content-Length", str(len(body)))
        conn.endheaders(body if body is not None else None)
        resp = conn.getresponse()
        payload = resp.read()
        return {
            "status": resp.status,
            "content_type": resp.getheader("Content-Type"),
            "response_bytes": len(payload),
            "response_sha256": _sha256_bytes(payload),
            "failure_class": None,
        }
    except socket.timeout:
        return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "failure_class": "deadline"}
    except OSError as exc:
        failure = "deadline" if "timed out" in str(exc).lower() else "transport"
        return {"status": None, "content_type": None, "response_bytes": 0, "response_sha256": None, "failure_class": failure, "error": str(exc)}
    finally:
        conn.close()


def _evaluate_expectation(expectation: Expectation, wire: Dict[str, Any]) -> Dict[str, Any]:
    checks = expectation.checks or {}
    unsupported = sorted(k for k in checks if k != "status")
    if unsupported:
        return {"expectation_result": "inconclusive", "expectation_detail": {"unsupported_checks": unsupported}}
    if "status" not in checks:
        return {"expectation_result": "inconclusive", "expectation_detail": {"reason": "no supported checks"}}
    allowed = [int(x) for x in checks["status"]]
    status = wire.get("status")
    if status in allowed:
        return {"expectation_result": "pass", "expectation_detail": {"status": status, "allowed_status": allowed}}
    return {"expectation_result": "violation", "expectation_detail": {"status": status, "allowed_status": allowed}}


def _safe_workdir(applications_root: Path, index: int, case: Case) -> Path:
    opaque = _sha256_bytes(f"{index}\0{case.case_id}".encode("utf-8"))[:16]
    workdir = applications_root / f"{index:04d}-{opaque}"
    apps_resolved = applications_root.resolve()
    parent_resolved = workdir.parent.resolve()
    if parent_resolved != apps_resolved:
        raise VerificationError("application workdir escaped applications root")
    return workdir


def _not_executed_receipt(case: Case, reason: str) -> Dict[str, Any]:
    return {
        "case_id": case.case_id,
        "provenance": list(case.provenance),
        "method": case.request.method,
        "path": case.request.path,
        "body_kind": case.request.body_kind,
        "request_headers": [list(h) for h in case.request.headers],
        "request_identity": case.identity_key(),
        "status": None,
        "content_type": None,
        "response_bytes": 0,
        "response_sha256": None,
        "failure_class": "not_executed",
        "expectation_result": "not_executed",
        "not_executed_reason": reason,
    }


def replay_suite(
    suite: Suite,
    base_url: Optional[str] = None,
    output_dir: Optional[Path] = None,
    mutate_resource: Optional[Dict[str, str]] = None,
    target: Optional[PerApplicationHttpTarget] = None,
) -> ReplayResult:
    if output_dir is None:
        raise VerificationError("output directory is required")
    if (base_url is None) == (target is None):
        raise VerificationError("provide exactly one of base_url or target")
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise VerificationError("output directory already exists")
    output_dir.mkdir(parents=True)
    applications_root = output_dir / "applications"
    applications_root.mkdir()
    receipts: List[Dict[str, Any]] = []
    applications: List[Dict[str, Any]] = []
    totals = {
        "planned": len(suite.cases),
        "attempted": 0,
        "completed": 0,
        "deadline_failures": 0,
        "transport_failures": 0,
        "http_failures": 0,
        "not_executed": 0,
        "expectation_passes": 0,
        "expectation_violations": 0,
        "expectation_inconclusive": 0,
    }
    abort_reason: Optional[str] = None
    for index, case in enumerate(suite.cases, start=1):
        if abort_reason is not None:
            receipts.append(_not_executed_receipt(case, abort_reason))
            totals["not_executed"] += 1
            continue

        totals["attempted"] += 1
        workdir = _safe_workdir(applications_root, index, case)
        pins_before: Dict[str, Dict[str, Any]] = {}
        if case.resource_package_id in suite.resources:
            pins_before = suite.resources[case.resource_package_id].copy_fresh_to(workdir)
        else:
            workdir.mkdir(parents=True, exist_ok=False)

        app_base_url = base_url
        target_quiet: Optional[bool] = None
        if target is not None:
            app_base_url = target.start(workdir)
        assert app_base_url is not None
        wire = _send_once(app_base_url, case.request, case.timeout_seconds)
        if target is not None:
            target_quiet = target.stop()
            if not target_quiet:
                abort_reason = "cannot prove target quiet after controlled lifecycle stop"

        if mutate_resource:
            for rel, content in mutate_resource.items():
                rel_path = Path(rel)
                if rel_path.is_absolute() or ".." in rel_path.parts:
                    raise VerificationError("mutate_resource path escapes workdir")
                target_file = workdir / rel_path
                if workdir.resolve() not in target_file.resolve().parents and target_file.resolve() != workdir.resolve():
                    raise VerificationError("mutate_resource path containment failure")
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content, encoding="utf-8")
        pins_after = hash_directory(workdir)
        failure = wire.get("failure_class")
        expectation_wire = {"expectation_result": "not_evaluated", "expectation_detail": {}}
        if failure is None:
            totals["completed"] += 1
            expectation_wire = _evaluate_expectation(case.expectation, wire)
            if expectation_wire["expectation_result"] == "pass":
                totals["expectation_passes"] += 1
            elif expectation_wire["expectation_result"] == "violation":
                totals["expectation_violations"] += 1
            else:
                totals["expectation_inconclusive"] += 1
        elif failure == "deadline":
            totals["deadline_failures"] += 1
            if target is None:
                abort_reason = "cannot prove target quiet after deadline on uncontrolled static target"
        else:
            totals["transport_failures"] += 1

        receipt = {
            "case_id": case.case_id,
            "provenance": list(case.provenance),
            "method": case.request.method,
            "path": case.request.path,
            "body_kind": case.request.body_kind,
            "request_headers": [list(h) for h in case.request.headers],
            "request_identity": case.identity_key(),
            **wire,
            **expectation_wire,
        }
        receipts.append(receipt)
        applications.append({
            "case_id": case.case_id,
            "workdir": str(workdir),
            "pins_before": pins_before,
            "pins_after": pins_after,
            "failure_class": failure,
            "target_quiet": target_quiet,
        })
    (output_dir / "receipts.json").write_text(json.dumps(receipts, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "applications.json").write_text(json.dumps(applications, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "totals.json").write_text(json.dumps(totals, indent=2, sort_keys=True), encoding="utf-8")
    return ReplayResult(totals, receipts, applications, output_dir)
