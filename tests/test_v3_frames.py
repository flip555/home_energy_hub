import importlib.util
import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures" / "v3"


def load(name):
    module_path = BASE / "custom_components/home_energy_hub/integrations/seplos_v3/data_parser.py"
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v3 = load("v3_data_parser")


def fixture(name):
    return json.loads((FIX / name).read_text())


class V3FrameTests(unittest.TestCase):
    def test_pia_frame(self):
        data = fixture("pia_sp05b.json")
        self.assertTrue(v3.verify_crc(data["frame_hex"]))
        pia = v3.decode_pia_response(data["frame_hex"])
        self.assertIsNotNone(pia)
        for key, expected in data["expected"].items():
            self.assertAlmostEqual(getattr(pia, key), expected, places=4, msg=key)

    def test_pib_frame(self):
        data = fixture("pib_sp05b.json")
        self.assertTrue(v3.verify_crc(data["frame_hex"]))
        pib = v3.decode_pib_response(data["frame_hex"])
        self.assertIsNotNone(pib)
        for key, expected in data["expected"].items():
            self.assertAlmostEqual(getattr(pib, key), expected, places=4, msg=key)

    def test_bad_crc_rejected(self):
        data = fixture("pia_sp05b.json")
        raw = bytearray.fromhex(data["frame_hex"])
        raw[10] ^= 0xFF
        self.assertIsNone(v3.decode_pia_response(raw.hex()))

    def test_truncated_rejected(self):
        data = fixture("pib_sp05b.json")
        self.assertIsNone(v3.decode_pib_response(data["frame_hex"][:-8]))

    def test_via_frame(self):
        data = fixture("via_sp05b.json")
        via = v3.decode_via_response(data["via_frame_hex"], data["model_frame_hex"])
        self.assertIsNotNone(via)
        for key, expected in data["expected"].items():
            self.assertEqual(getattr(via, key), expected)

    def test_pic_bits(self):
        data = fixture("pic_sp05b.json")
        pic = v3.decode_pic_response_modbus(data["frame_hex"])
        self.assertIsNotNone(pic)
        self.assertEqual(len(pic.bits), data["expected"]["count"])
        self.assertEqual(sum(pic.bits), data["expected"]["on"])

    def test_sfa_bits(self):
        data = fixture("sfa_sp05b.json")
        sfa = v3.decode_sfa_response(data["frame_hex"])
        self.assertIsNotNone(sfa)
        self.assertEqual(len(sfa.bits), data["expected"]["count"])
        self.assertEqual(sum(sfa.bits), data["expected"]["on"])

    def test_spa_values(self):
        data = fixture("spa_sp05b.json")
        spa = v3.decode_spa_response(data["frame_hex"])
        self.assertIsNotNone(spa)
        self.assertEqual(len(spa.values), data["expected"]["count"])
        for addr, expected in data["expected"]["samples"].items():
            self.assertAlmostEqual(spa.values[addr], expected, places=6)

    def test_extract_all_frames(self):
        pia = fixture("pia_sp05b.json")["frame_hex"]
        pib = fixture("pib_sp05b.json")["frame_hex"]
        via = fixture("via_sp05b.json")
        pic = fixture("pic_sp05b.json")["frame_hex"]
        sfa = fixture("sfa_sp05b.json")["frame_hex"]
        spa = fixture("spa_sp05b.json")["frame_hex"]
        result = v3.extract_data_from_message(
            [pia, pib, via["via_frame_hex"], via["model_frame_hex"], pic, sfa, spa]
        )
        self.assertEqual(result["manufacturer"], via["expected"]["manufacturer"])
        self.assertEqual(len(result["pic_bits"]), 144)
        self.assertEqual(len(result["sfa_bits"]), 80)
        self.assertAlmostEqual(result["spa_1300"], 4.0)
