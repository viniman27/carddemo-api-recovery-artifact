#!/usr/bin/env python3
"""Executable finite MBT reference engine for P3 draft v4.

Stdlib-only. Guard evaluation is manual: no Python eval/exec.
The validator contains targeted capability-scoped event checks; these are not
claimed as an automatic proof of COBOL semantics.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any


class ModelError(Exception):
    pass


class ValidationError(ModelError):
    pass


TRUTH = {True, False, "unknown"}
GUARD_OPS = {"true", "eq", "ne", "and", "or", "not", "in", "gte", "lte", "unknown"}
EFFECT_OPS = {"set", "inc", "emit", "assert", "clear_events"}
EVENTS = {
    "open_attempt", "abend", "close_attempt", "daily_read_attempt", "daily_record_counted",
    "reject_write_attempt", "tcatbal_update_attempt", "account_rewrite_attempt",
    "account_rewrite_invalid_key_continues", "tranfile_write_attempt_pending", "tranfile_write_attempt",
    "intcalc_open_attempt", "tcatbal_read_attempt", "group_start", "interest_compute_attempt",
    "interest_write_attempt", "account_update_attempt", "intcalc_eof_no_final_account_update",
    "report_open_attempt", "report_read_attempt", "report_detail_attempt", "account_accrual_attempt",
    "tranrept_skip_detail_out_of_range", "page_total_attempt", "grand_total_attempt",
    "unknown_eof_receiver_path", "account_total_attempt", "lookup_attempt",
    "interest_rate_zero_no_interest_write"
}

# Targeted source-derived capability scopes for observable/control events.
# This prevents cross-capability reuse of a known event name (for example,
# interest_write_attempt in POSTTRAN) without claiming full semantic proof.
EVENT_CAPABILITY_SCOPES = {
    "open_attempt": {"CBTRN02C_POSTTRAN"},
    "daily_read_attempt": {"CBTRN02C_POSTTRAN"},
    "daily_record_counted": {"CBTRN02C_POSTTRAN"},
    "reject_write_attempt": {"CBTRN02C_POSTTRAN"},
    "tcatbal_update_attempt": {"CBTRN02C_POSTTRAN"},
    "account_rewrite_attempt": {"CBTRN02C_POSTTRAN"},
    "account_rewrite_invalid_key_continues": {"CBTRN02C_POSTTRAN"},
    "tranfile_write_attempt_pending": {"CBTRN02C_POSTTRAN"},
    "tranfile_write_attempt": {"CBTRN02C_POSTTRAN"},
    "intcalc_open_attempt": {"CBACT04C_INTCALC"},
    "tcatbal_read_attempt": {"CBACT04C_INTCALC"},
    "group_start": {"CBACT04C_INTCALC"},
    "interest_compute_attempt": {"CBACT04C_INTCALC"},
    "interest_write_attempt": {"CBACT04C_INTCALC"},
    "interest_rate_zero_no_interest_write": {"CBACT04C_INTCALC"},
    "account_update_attempt": {"CBACT04C_INTCALC"},
    "intcalc_eof_no_final_account_update": {"CBACT04C_INTCALC"},
    "report_open_attempt": {"CBTRN03C_TRANREPT"},
    "report_read_attempt": {"CBTRN03C_TRANREPT"},
    "report_detail_attempt": {"CBTRN03C_TRANREPT"},
    "account_accrual_attempt": {"CBTRN03C_TRANREPT"},
    "tranrept_skip_detail_out_of_range": {"CBTRN03C_TRANREPT"},
    "page_total_attempt": {"CBTRN03C_TRANREPT"},
    "grand_total_attempt": {"CBTRN03C_TRANREPT"},
    "unknown_eof_receiver_path": {"CBTRN02C_POSTTRAN", "CBTRN03C_TRANREPT"},
    "account_total_attempt": {"CBTRN03C_TRANREPT"},
    "lookup_attempt": {"CBTRN02C_POSTTRAN", "CBTRN03C_TRANREPT"},
    "close_attempt": {"CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"},
    "abend": {"CBTRN02C_POSTTRAN", "CBACT04C_INTCALC", "CBTRN03C_TRANREPT"},
}


def load_model(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def _cap(model: dict[str, Any], cap_id: str) -> dict[str, Any]:
    for c in model.get("capabilities", []):
        if c.get("id") == cap_id:
            return c
    raise ModelError(f"unknown capability {cap_id}")


def _domain(cap: dict[str, Any], name: str) -> list[Any]:
    return cap.get("variables", {}).get(name, {}).get("domain", [])


def _type(cap: dict[str, Any], name: str) -> str | None:
    return cap.get("variables", {}).get(name, {}).get("type")


def _value(expr: dict[str, Any], valuation: dict[str, Any], cap: dict[str, Any]) -> Any:
    if "var" in expr:
        v = expr["var"]
        if v not in cap.get("variables", {}):
            raise ModelError(f"unknown variable {v}")
        return valuation.get(v, cap["variables"][v].get("initial"))
    if "value" in expr:
        return expr["value"]
    raise ModelError(f"invalid value expr {expr}")


def eval_guard(guard: dict[str, Any], valuation: dict[str, Any], cap: dict[str, Any]) -> bool | str:
    op = guard.get("op")
    if op not in GUARD_OPS:
        raise ModelError(f"unknown guard op {op}")
    if op == "true":
        return True
    if op == "unknown":
        return "unknown" if valuation.get(guard["var"]) == "UnknownEOF" else False
    if op in {"eq", "ne", "gte", "lte"}:
        left = _value(guard["left"], valuation, cap)
        right = _value(guard["right"], valuation, cap)
        if left == "UnknownEOF" or right == "UnknownEOF":
            return False
        if op == "eq": return left == right
        if op == "ne": return left != right
        if op == "gte": return left >= right
        if op == "lte": return left <= right
    if op == "in":
        left = _value(guard["left"], valuation, cap)
        return left != "UnknownEOF" and left in guard.get("values", [])
    if op == "not":
        r = eval_guard(guard["arg"], valuation, cap)
        return "unknown" if r == "unknown" else not r
    if op == "and":
        saw_unknown = False
        for g in guard.get("args", []):
            r = eval_guard(g, valuation, cap)
            if r is False:
                return False
            saw_unknown = saw_unknown or r == "unknown"
        return "unknown" if saw_unknown else True
    if op == "or":
        saw_unknown = False
        for g in guard.get("args", []):
            r = eval_guard(g, valuation, cap)
            if r is True:
                return True
            saw_unknown = saw_unknown or r == "unknown"
        return "unknown" if saw_unknown else False
    raise ModelError(f"unhandled guard op {op}")


def apply_effect(state: dict[str, Any], effect: dict[str, Any], cap: dict[str, Any]) -> dict[str, Any]:
    op = effect.get("op")
    if op not in EFFECT_OPS:
        raise ModelError(f"unknown effect op {op}")
    nxt = copy.deepcopy(state)
    vals = nxt.setdefault("values", {})
    vals.setdefault("events", [])
    vals.setdefault("attempts", [])
    if op == "set":
        vals[effect["var"]] = effect["value"]
    elif op == "inc":
        vals[effect["var"]] = int(vals.get(effect["var"], 0)) + int(effect.get("by", 1))
    elif op == "emit":
        ev = effect["event"]
        vals["events"].append(ev)
        if ev.endswith("_attempt") or ev.endswith("_pending"):
            vals["attempts"].append(ev)
    elif op == "assert":
        got = vals.get(effect["var"])
        if got != effect["equals"]:
            raise ModelError(f"assert failed {effect['var']}={got!r} expected {effect['equals']!r}")
    elif op == "clear_events":
        vals["events"] = []
    return nxt


def _initial_state(cap: dict[str, Any], state_id: str | None = None, valuation: dict[str, Any] | None = None) -> dict[str, Any]:
    vals = {k: v.get("initial") for k, v in cap.get("variables", {}).items() if "initial" in v}
    vals.update({"events": [], "attempts": []})
    if valuation:
        vals.update(valuation)
    return {"state": state_id or cap["initialState"], "values": vals}


def step(model: dict[str, Any], cap_id: str, state_id: str, valuation: dict[str, Any]) -> list[dict[str, Any]]:
    cap = _cap(model, cap_id)
    current = _initial_state(cap, state_id, valuation)
    out = []
    for tr in sorted(cap.get("transitions", []), key=lambda x: x["id"]):
        if tr["from"] != state_id:
            continue
        r = eval_guard(tr["guard"], current["values"], cap)
        if r is True or r == "unknown":
            nxt = copy.deepcopy(current)
            for eff in tr.get("effects", []):
                nxt = apply_effect(nxt, eff, cap)
            nxt["state"] = tr["to"]
            out.append({"transitionId": tr["id"], "guardResult": r, "state": nxt})
    return out


def _witness_guard(g: dict[str, Any]) -> dict[str, Any]:
    op = g.get("op")
    if op in {"eq", "gte", "lte"} and isinstance(g.get("left"), dict) and "var" in g["left"] and isinstance(g.get("right"), dict) and "value" in g["right"]:
        return {g["left"]["var"]: g["right"]["value"]}
    if op == "in" and isinstance(g.get("left"), dict) and "var" in g["left"] and g.get("values"):
        return {g["left"]["var"]: g["values"][0]}
    if op == "unknown":
        return {g["var"]: "UnknownEOF"}
    if op == "and":
        out: dict[str, Any] = {}
        for x in g.get("args", []):
            out.update(_witness_guard(x))
        return out
    return {}


def _enabled_for_traversal(model: dict[str, Any], cap: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for tr in sorted(cap.get("transitions", []), key=lambda x: x["id"]):
        if tr["from"] != state["state"]:
            continue
        vals = copy.deepcopy(state["values"])
        vals.update(_witness_guard(tr["guard"]))
        for k, spec in cap.get("variables", {}).items():
            vals.setdefault(k, spec.get("initial"))
        r = eval_guard(tr["guard"], vals, cap)
        if r is True or r == "unknown":
            nxt = {"state": state["state"], "values": vals}
            for eff in tr.get("effects", []):
                nxt = apply_effect(nxt, eff, cap)
            nxt["state"] = tr["to"]
            out.append({"transitionId": tr["id"], "guardResult": r, "state": nxt})
    return out


def traverse(model: dict[str, Any], cap_id: str, max_depth: int, max_paths: int) -> dict[str, Any]:
    cap = _cap(model, cap_id)
    queue = deque([(_initial_state(cap), [])])
    completed, frontier, unknown = [], [], []
    emitted = 0
    omitted = 0
    loop_visits: dict[str, int] = {}
    per_state_seen: dict[str, int] = {}
    bounds = cap.get("loopPolicy", {}).get("bounds", {})
    loop_states = set(cap.get("loopPolicy", {}).get("loopStates", []))
    while queue:
        state, path = queue.popleft()
        sid = state["state"]
        if sid in loop_states:
            per_state_seen[sid] = per_state_seen.get(sid, 0) + 1
            loop_visits[sid] = min(per_state_seen[sid], sum(bounds.values()) + 1 if bounds else per_state_seen[sid])
            if bounds and per_state_seen[sid] > sum(bounds.values()) + 1:
                omitted += 1
                continue
        if len(path) >= max_depth:
            frontier.append({"state": sid, "path": path})
            omitted += 1
            continue
        outgoing = _enabled_for_traversal(model, cap, state)
        if not outgoing:
            completed.append({"state": sid, "path": path, "events": state["values"].get("events", [])})
            continue
        for item in outgoing:
            npath = path + [item["transitionId"]]
            if item["guardResult"] == "unknown":
                unknown.append({"state": item["state"]["state"], "path": npath})
            if emitted < max_paths:
                queue.append((item["state"], npath)); emitted += 1
            else:
                omitted += 1
    return {"capability": cap_id, "completed": completed, "frontier": frontier, "unknown": unknown, "omittedCount": omitted, "loopVisits": loop_visits, "budget": {"maxDepth": max_depth, "maxPaths": max_paths}}


def _check_literal(expr: dict[str, Any], cap: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(expr, dict):
        errors.append("literal expr is not object"); return
    if "var" in expr:
        if expr["var"] not in cap.get("variables", {}): errors.append(f"unknown variable {expr['var']}")
        return
    if "value" in expr:
        typ = expr.get("type")
        val = expr["value"]
        if typ == "bool" and not isinstance(val, bool): errors.append(f"literal {val!r} not bool")
        if typ == "int" and not isinstance(val, int): errors.append(f"literal {val!r} not int")
        if typ == "enum":
            domains = [set(v.get("domain", [])) for v in cap.get("variables", {}).values()]
            if not any(val in d for d in domains): errors.append(f"literal {val!r} not in any declared domain")
        return
    errors.append(f"bad literal expr {expr}")


def _check_guard(g: dict[str, Any], cap: dict[str, Any], errors: list[str]) -> None:
    op = g.get("op")
    if op not in GUARD_OPS: errors.append(f"unknown guard op {op}"); return
    if op in {"eq", "ne", "gte", "lte"}:
        _check_literal(g.get("left"), cap, errors); _check_literal(g.get("right"), cap, errors)
        if isinstance(g.get("left"), dict) and "var" in g["left"] and isinstance(g.get("right"), dict) and "value" in g["right"]:
            var = g["left"]["var"]; val = g["right"]["value"]
            dom = _domain(cap, var)
            if val not in dom: errors.append(f"literal {val!r} outside domain of {var}")
            if _type(cap, var) == "bool" and not isinstance(val, bool): errors.append(f"literal for {var} must be bool")
            if _type(cap, var) != "bool" and isinstance(val, bool): errors.append(f"literal for {var} cannot be bool")
    elif op in {"and", "or"}:
        for x in g.get("args", []): _check_guard(x, cap, errors)
    elif op == "not": _check_guard(g.get("arg", {}), cap, errors)
    elif op == "unknown":
        if g.get("var") not in cap.get("variables", {}): errors.append(f"unknown variable {g.get('var')}")
    elif op == "in":
        _check_literal(g.get("left"), cap, errors)


def validate_source_pins(model: dict[str, Any], root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    corpus = root.parent / "reference-authoring-input-v1" / "corpus"
    errors, checked = [], 0
    cache: dict[str, tuple[str, int]] = {}
    for cap in model.get("capabilities", []):
        for tr in cap.get("transitions", []):
            for a in tr.get("sourceAnchors", []):
                p = corpus / a["path"]
                if not p.exists():
                    errors.append(f"missing source {a['path']}"); continue
                if a["path"] not in cache:
                    data = p.read_bytes()
                    cache[a["path"]] = (hashlib.sha256(data).hexdigest(), len(p.read_text(encoding='utf-8', errors='replace').splitlines()))
                sha, nlines = cache[a["path"]]
                if sha != a.get("sha256"): errors.append(f"sha mismatch {a['path']}")
                lo, hi = a.get("lines", [0, 0])
                if not (1 <= lo <= hi <= nlines): errors.append(f"bad line interval {a['path']}:{lo}-{hi}/{nlines}")
                checked += 1
    return {"errors": errors, "checkedAnchors": checked, "checkedFiles": len(cache)}


def validate_model(model: dict[str, Any], root: str | Path | None = None, raise_on_error: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    if model.get("status") != "draft_needs_review": errors.append("status must be draft_needs_review")
    obligation_ids = {o["id"] for o in model.get("obligations", [])}
    referenced_obligations: set[str] = set()
    all_states = 0; all_transitions = 0
    for cap in model.get("capabilities", []):
        states = {s["id"] for s in cap.get("states", [])}; all_states += len(states)
        if cap.get("initialState") not in states: errors.append(f"bad initial state {cap.get('id')}")
        for name, spec in cap.get("variables", {}).items():
            if "domain" not in spec or not spec["domain"]: errors.append(f"empty domain {cap['id']}.{name}")
            parts = spec.get("partitions", [])
            if parts and sorted(sum((p.get("values", []) for p in parts), []), key=str) != sorted(spec["domain"], key=str):
                errors.append(f"partitions do not cover domain {cap['id']}.{name}")
        for tr in cap.get("transitions", []):
            all_transitions += 1
            if tr.get("from") not in states or tr.get("to") not in states: errors.append(f"bad state ref {tr.get('id')}")
            _check_guard(tr.get("guard", {}), cap, errors)
            for eff in tr.get("effects", []):
                if eff.get("op") not in EFFECT_OPS: errors.append(f"unknown effect {eff.get('op')} in {tr.get('id')}")
                if eff.get("op") == "emit":
                    event = eff.get("event")
                    if event not in EVENTS:
                        errors.append(f"unknown event {event} in {tr.get('id')}")
                    elif cap.get("id") not in EVENT_CAPABILITY_SCOPES.get(event, set()):
                        errors.append(f"event {event} not source-scoped to {cap.get('id')} in {tr.get('id')}")
            for ref in tr.get("obligationRefs", []):
                referenced_obligations.add(ref)
                if ref not in obligation_ids: errors.append(f"broken obligation ref {ref} in {tr.get('id')}")
    missing_obligation_refs = sorted(obligation_ids - referenced_obligations)
    if missing_obligation_refs:
        errors.append(f"obligations without reachable transition refs {missing_obligation_refs}")
    # source-sensitive obligation checks for reviewed FAIL-06/v3-block mutants; intentionally not generic proof.
    req = {
        "POSTTRAN-T020": {"must": {"account_rewrite_invalid_key_continues", "tranfile_write_attempt_pending"}, "must_not": {"abend"}, "anchor": "POSTTRAN-OBL-008"},
        "TRANREPT-T009": {"must": {"tranrept_skip_detail_out_of_range"}, "must_not": {"report_detail_attempt", "account_accrual_attempt"}, "anchor": "TRANREPT-OBL-003"},
        "INTCALC-T006": {"must": {"intcalc_eof_no_final_account_update"}, "must_not": {"account_update_attempt"}, "anchor": "INTCALC-OBL-008"},
    }
    for tid, rule in req.items():
        found = None
        for cap in model.get("capabilities", []):
            for tr in cap.get("transitions", []):
                if tr.get("id") == tid: found = tr
        if not found: errors.append(f"missing source-sensitive transition {tid}"); continue
        evs = {e.get("event") for e in found.get("effects", []) if e.get("op") == "emit"}
        if not rule["must"].issubset(evs): errors.append(f"{tid} missing required source-anchored events")
        if rule["must_not"] & evs: errors.append(f"{tid} contains forbidden source-anchored events {rule['must_not'] & evs}")
        if rule["anchor"] not in found.get("obligationRefs", []): errors.append(f"{tid} missing obligation anchor {rule['anchor']}")
    if root is not None:
        errors.extend(validate_source_pins(model, root)["errors"])
    report = {"status": model.get("status"), "errors": errors, "counts": {"capabilities": len(model.get("capabilities", [])), "states": all_states, "transitions": all_transitions, "obligations": len(obligation_ids)}}
    if errors and raise_on_error: raise ValidationError("; ".join(errors))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--traverse", action="append", default=[])
    ap.add_argument("--max-depth", type=int, default=8)
    ap.add_argument("--max-paths", type=int, default=100)
    ns = ap.parse_args(argv)
    root = Path(ns.root).resolve()
    model = load_model(root / "model.json")
    report = validate_model(model, root=root)
    report["sourcePins"] = validate_source_pins(model, root)
    report["traversals"] = {cid: traverse(model, cid, ns.max_depth, ns.max_paths) for cid in ns.traverse}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
