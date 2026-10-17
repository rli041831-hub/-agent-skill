"""Generate a task-owned interview fragment; never sends a message."""
import argparse
import hashlib
import json
from pathlib import Path


def render(config):
    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    required = ("schema", "title", "followup")
    for key in required:
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f"{key} must be nonempty text")
    if type(config.get("round")) is not int or config["round"] < 1:
        raise ValueError("round must be a positive integer")
    questions = config.get("questions")
    if not isinstance(questions, list) or not 1 <= len(questions) <= 4:
        raise ValueError("questions must contain 1–4 items")
    for q in questions:
        if not isinstance(q, dict) or not isinstance(q.get("title"), str) or not q["title"].strip():
            raise ValueError("question title required")
        opts = q.get("options")
        if not isinstance(opts, list) or not 1 <= len(opts) <= 10 or any(not isinstance(x, str) or not x.strip() for x in opts):
            raise ValueError("each question needs 1–10 nonempty options")
        if len(set(opts)) != len(opts):
            raise ValueError("duplicate options")
        if "hint" in q and not isinstance(q["hint"], str):
            raise ValueError("hint must be text")
    raw = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode("utf-8")) > 18000:
        raise ValueError("configuration too large; shorten this interview round")
    root = "idea-interview-" + hashlib.sha256(config["schema"].encode()).hexdigest()[:12]
    # JSON escapes defeat closing-script injection; labels are assigned via textContent.
    safe = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (Path(__file__).resolve().parents[1] / "assets" / "interview-fragment.html").read_text(encoding="utf-8")
    return template.replace("__ROOT_ID__", root).replace("__CONFIG_JSON__", safe)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        content = render(json.loads(args.config.read_text(encoding="utf-8-sig")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w" if args.overwrite else "x", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Interview not generated: {error}\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
