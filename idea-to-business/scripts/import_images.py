"""Archive five explicitly mapped local originals; no downloads or content approval.

Requires Pillow. Input paths are relative to the mapping JSON, or absolute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import warnings

from PIL import Image
from handoff_state import identity, load_manifest, read_json


TRANSPORTS = {"browser-download", "download-folder", "user-upload"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_image(path):
    data = path.read_bytes()
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as im:
            if im.format not in {"PNG", "JPEG", "WEBP"} or getattr(im, "n_frames", 1) != 1:
                raise ValueError("only static PNG/JPEG/WebP originals supported")
            im.verify()
        with Image.open(path) as im:
            im.load()
            rgba = im.convert("RGBA")
            pixels = str(im.size).encode() + rgba.tobytes()
            return {"sha256": digest(data), "pixel_sha256": digest(pixels), "bytes": len(data),
                    "width": im.width, "height": im.height, "format": im.format}


def validate_mapping(manifest, mapping, base):
    if any(mapping.get(k) != v for k, v in identity(manifest).items()):
        raise ValueError("mapping must identify this exact handoff, content hash and round")
    expected = {v["id"] for v in manifest["variants"]}
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", v) for v in expected):
        raise ValueError("variant IDs must be safe filename components")
    images = mapping.get("images")
    if (not isinstance(images, list) or len(images) != 5 or
            any(not isinstance(r, dict) for r in images) or
            {r.get("variant_id") for r in images} != expected):
        raise ValueError("exactly one mapped original per variant required")
    records = []
    for record in images:
        if record.get("transport") not in TRANSPORTS or not isinstance(record.get("source_evidence"), str) or not record["source_evidence"].strip():
            raise ValueError("each file needs transport and current-reply attribution evidence")
        if not isinstance(record.get("path"), str) or not record["path"]:
            raise ValueError("each file needs a path")
        path = Path(record["path"])
        if not path.is_absolute():
            path = base / path
        path = path.resolve(strict=True)
        info = inspect_image(path)
        records.append({**record, "source_path": str(path), **info})
    if len({r["pixel_sha256"] for r in records}) != 5:
        raise ValueError("duplicate image pixels: five distinct originals required")
    return records


def import_images(manifest, mapping, destination, base=Path(".")):
    records = validate_mapping(manifest, mapping, base)
    destination = Path(destination)
    if destination.exists():
        receipt = read_json(destination / "import-receipt.json")
        if any(receipt.get(k) != v for k, v in identity(manifest).items()):
            raise ValueError("destination belongs to another handoff")
        existing = {r["variant_id"]: r for r in receipt["images"]}
        if len(existing) != 5:
            raise ValueError("existing receipt is incomplete")
        for record in records:
            old = existing.get(record["variant_id"], {})
            if any(old.get(k) != record.get(k) for k in ("sha256", "pixel_sha256", "transport", "source_evidence")):
                raise ValueError("existing import differs; choose a new destination")
            archived = (destination / old["image_ref"]).resolve()
            if not archived.is_relative_to(destination.resolve()) or digest(archived.read_bytes()) != old["sha256"]:
                raise ValueError("archived file changed or escaped destination")
        return receipt
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".image-import-", dir=destination.parent))
    try:
        for record in records:
            extension = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[record["format"]]
            record["image_ref"] = record["variant_id"] + extension
            shutil.copyfile(record["source_path"], stage / record["image_ref"])
            if digest((stage / record["image_ref"]).read_bytes()) != record["sha256"]:
                raise ValueError("source changed during import")
            record["review_status"] = "pending"
        receipt = {**identity(manifest), "schema": "idea-to-business-image-import-v1", "images": records,
                   "status": "files-imported-not-content-approved", "user_choice": None,
                   "attribution_notice": "Source evidence supplied by operator; not independently proven by script."}
        (stage / "import-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        # Rename publishes a complete batch; never overwrite a previous destination.
        stage.rename(destination)
        return receipt
    finally:
        if stage.exists():
            if stage.resolve().parent != destination.parent.resolve() or not stage.name.startswith(".image-import-"):
                raise RuntimeError("refuse cleanup outside the intended import parent")
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        receipt = import_images(load_manifest(args.manifest), read_json(args.mapping), args.destination,
                                args.mapping.resolve().parent)
        print(json.dumps({"status": receipt["status"], "count": len(receipt["images"])}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        parser.exit(2, f"Images not imported: {error}\n")


if __name__ == "__main__":
    main()
