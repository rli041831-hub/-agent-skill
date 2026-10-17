"""Persist a send-once reservation and observations. Never sends messages."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from build_handoff import prepare


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_manifest(path):
    manifest = read_json(path)
    verified = prepare(manifest)
    for field in ("handoff_id", "content_hash"):
        if manifest.get(field) != verified[field]:
            raise ValueError(f"manifest {field} mismatch")
    return manifest


def identity(manifest):
    return {key: manifest[key] for key in ("handoff_id", "content_hash", "round")}


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".pending-", delete=False) as stream:
            name = stream.name
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(path):
    """A leftover lock requires inspection, never an automatic force-unlock."""
    lock = Path(str(path) + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, f"pid={os.getpid()} at={now()}".encode())
        os.close(fd)
        fd = None
        yield
    finally:
        if fd is not None:
            os.close(fd)
        lock.unlink()


def reserve(manifest, state_path, target, authorization_ref, mode_evidence):
    if not all(isinstance(s, str) and s.strip() for s in (target, authorization_ref, mode_evidence)):
        raise ValueError("target, authorization and current Chat-mode evidence are required")
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with locked(state_path):
        if state_path.exists():
            state = read_json(state_path)
            if any(state.get(k) != v for k, v in identity(manifest).items()) or state.get("target") != target:
                raise ValueError("state already belongs to a different handoff or target")
            raise ValueError("send already reserved: observe target; do not resend")
        state = {**identity(manifest), "schema": "idea-to-business-send-state-v1", "target": target,
                 "authorization_ref": authorization_ref, "chat_mode_evidence": mode_evidence,
                 "state": "send-reserved-outcome-unknown", "send_reservation_count": 1,
                 "automatic_resend_allowed": False,
                 "events": [{"at": now(), "type": "send-reserved", "evidence": "reserved before send click"}]}
        atomic_json(state_path, state)
    return state


STATES = {"message-present": "message-observed", "five-generated": "five-generated",
          "retrieval-failed": "retrieval-blocked", "files-imported": "files-await-review"}


def observe(manifest, state_path, target, event, evidence):
    if event not in STATES or not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("supported observation and evidence required")
    state_path = Path(state_path)
    with locked(state_path):
        state = read_json(state_path)
        if any(state.get(k) != v for k, v in identity(manifest).items()) or state.get("target") != target:
            raise ValueError("observation belongs to a different handoff or target")
        seen = {e["type"] for e in state["events"]}
        if event in {"five-generated", "retrieval-failed", "files-imported"} and "message-present" not in seen:
            raise ValueError("first observe the matching sent message")
        if event in {"retrieval-failed", "files-imported"} and "five-generated" not in seen:
            raise ValueError("first verify the five images belong to this reply")
        state["events"].append({"at": now(), "type": event, "evidence": evidence})
        state["state"] = STATES[event]
        atomic_json(state_path, state)
    return state


def next_action(state):
    seen = {e["type"] for e in state["events"]}
    if "files-imported" in seen:
        return "review-current-originals; do-not-resend"
    if "five-generated" in seen:
        return "retrieve-existing-images-only; do-not-resend"
    return "read-target-for-this-handoff-id; do-not-resend"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["reserve", "observe", "status"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("--target")
    parser.add_argument("--authorization-ref")
    parser.add_argument("--mode-evidence")
    parser.add_argument("--event", choices=list(STATES))
    parser.add_argument("--evidence")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.action == "reserve":
            state = reserve(manifest, args.state, args.target, args.authorization_ref, args.mode_evidence)
        elif args.action == "observe":
            state = observe(manifest, args.state, args.target, args.event, args.evidence)
        else:
            state = read_json(args.state)
            if any(state.get(k) != v for k, v in identity(manifest).items()):
                raise ValueError("state identity mismatch")
        print(json.dumps({"state": state["state"], "next_action": next_action(state)}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"State not changed: {error}\n")


if __name__ == "__main__":
    main()
