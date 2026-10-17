"""Behavior checks for crash recovery and original-file import; no remote actions."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "idea-to-business"
if not SKILL.exists():
    SKILL = ROOT / "idea-to-business"
sys.path.insert(0, str(SKILL / "scripts"))
from build_handoff import prepare
from handoff_state import identity, next_action, observe, reserve
from import_images import import_images


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        data = json.loads((SKILL / "assets" / "handoff-input.json").read_text(encoding="utf-8"))
        self.manifest = prepare(data)
        self.state_path = self.root / "state.json"
        self.mapping = {**identity(self.manifest), "images": []}
        for i in range(1, 6):
            image = self.root / f"source{i}.png"
            Image.new("RGB", (24, 40), (i * 30, 20, 50)).save(image)
            self.mapping["images"].append({"variant_id": f"V{i}", "path": image.name,
                "transport": "user-upload", "source_evidence": f"synthetic test image {i}, not a live reply"})

    def tearDown(self):
        self.temp.cleanup()

    def reserve(self):
        return reserve(self.manifest, self.state_path, "test-chat", "test-only-authorization", "simulated Chat-mode observation")

    def record(self, event):
        return observe(self.manifest, self.state_path, "test-chat", event, "synthetic observation")

    def run_import(self, mapping=None):
        return import_images(self.manifest, mapping or self.mapping, self.root / "originals", self.root)

    def test_unknown_send_outcome_never_releases_reservation(self):
        self.reserve()
        with self.assertRaises(ValueError):
            self.reserve()
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertFalse(state["automatic_resend_allowed"])
        self.assertIn("read-target", next_action(state))

    def test_concurrent_reservations_only_one_succeeds(self):
        def attempt():
            try:
                self.reserve()
                return True
            except (ValueError, FileExistsError):
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(lambda _: attempt(), range(2))), 1)

    def test_other_target_cannot_update_state(self):
        self.reserve()
        before = self.state_path.read_bytes()
        with self.assertRaises(ValueError):
            observe(self.manifest, self.state_path, "other-chat", "message-present", "test")
        self.assertEqual(before, self.state_path.read_bytes())

    def test_different_round_cannot_update_state(self):
        self.reserve()
        changed = {**self.manifest, "round": 2}
        with self.assertRaises(ValueError):
            observe(changed, self.state_path, "test-chat", "message-present", "test")

    def test_five_images_require_matching_message_observation(self):
        self.reserve()
        with self.assertRaises(ValueError):
            self.record("five-generated")

    def test_failed_retrieval_recovers_without_resend(self):
        self.reserve()
        self.record("message-present")
        self.record("five-generated")
        state = self.record("retrieval-failed")
        self.assertIn("retrieve-existing-images-only", next_action(state))
        with self.assertRaises(ValueError):
            self.reserve()

    def test_import_retains_original_bytes_and_pending_status(self):
        receipt = self.run_import()
        self.assertEqual(len(receipt["images"]), 5)
        self.assertIsNone(receipt["user_choice"])
        for image in receipt["images"]:
            self.assertEqual(image["review_status"], "pending")
            self.assertEqual((self.root / image["path"]).read_bytes(), (self.root / "originals" / image["image_ref"]).read_bytes())
            self.assertEqual(image["transport"], "user-upload")

    def test_same_import_is_idempotent(self):
        first = self.run_import()
        self.assertEqual(first, self.run_import())

    def test_changed_archived_file_rejected(self):
        self.run_import()
        (self.root / "originals" / "V1.png").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.run_import()

    def test_wrong_content_hash_rejected_before_output(self):
        self.mapping["content_hash"] = "wrong"
        with self.assertRaises(ValueError):
            self.run_import()
        self.assertFalse((self.root / "originals").exists())

    def test_missing_or_duplicate_variant_rejected(self):
        self.mapping["images"][-1]["variant_id"] = "V1"
        with self.assertRaises(ValueError):
            self.run_import()

    def test_same_pixels_with_different_metadata_rejected(self):
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("different", "metadata")
        with Image.open(self.root / "source1.png") as image:
            image.save(self.root / "source2.png", pnginfo=metadata)
        self.assertNotEqual((self.root / "source1.png").read_bytes(), (self.root / "source2.png").read_bytes())
        with self.assertRaisesRegex(ValueError, "duplicate image pixels"):
            self.run_import()

    def test_truncated_image_rejected_without_partial_delivery(self):
        (self.root / "source5.png").write_bytes(b"not an image")
        with self.assertRaises(OSError):
            self.run_import()
        self.assertFalse((self.root / "originals").exists())

    def test_copy_failure_leaves_no_half_batch(self):
        with patch("import_images.shutil.copyfile", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.run_import()
        self.assertFalse((self.root / "originals").exists())
        self.assertEqual(list(self.root.glob(".image-import-*")), [])

    def test_screenshot_or_old_image_not_certified_by_file_check(self):
        receipt = self.run_import()
        self.assertIn("not-content-approved", receipt["status"])
        self.assertIn("not independently proven", receipt["attribution_notice"])

    def test_provenance_required_and_cannot_silently_change(self):
        self.run_import()
        changed = copy.deepcopy(self.mapping)
        changed["images"][0]["transport"] = "browser-download"
        with self.assertRaises(ValueError):
            self.run_import(changed)


if __name__ == "__main__":
    unittest.main()
