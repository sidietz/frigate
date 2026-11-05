import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from frigate.detectors.plugins import hailo


class TestHailoDetector(unittest.TestCase):
    def test_detect_hailo_arch_hailo10h(self):
        fake_output = (
            "Firmware Version: 5.2.0\n"
            "Device Architecture: HAILO10H\n"
            "Serial Number: 12345\n"
        )
        mock_result = MagicMock(returncode=0, stdout=fake_output, stderr="")
        with patch("subprocess.run", return_value=mock_result), patch(
            "frigate.detectors.plugins.hailo.find_tool", return_value="hailortcli"
        ):
            arch = hailo.detect_hailo_arch()
            self.assertEqual(arch, "hailo10h")

    def test_detect_hailo_arch_hailo10(self):
        fake_output = (
            "Firmware Version: 5.2.0\n"
            "Device Architecture: HAILO10\n"
            "Serial Number: 12345\n"
        )
        mock_result = MagicMock(returncode=0, stdout=fake_output, stderr="")
        with patch("subprocess.run", return_value=mock_result), patch(
            "frigate.detectors.plugins.hailo.find_tool", return_value="hailortcli"
        ):
            arch = hailo.detect_hailo_arch()
            self.assertEqual(arch, "hailo10h")

    def test_detect_hailo_arch_hailo8l(self):
        fake_output = "Device Architecture: HAILO8L\n"
        mock_result = MagicMock(returncode=0, stdout=fake_output, stderr="")
        with patch("subprocess.run", return_value=mock_result), patch(
            "frigate.detectors.plugins.hailo.find_tool", return_value="hailortcli"
        ):
            arch = hailo.detect_hailo_arch()
            self.assertEqual(arch, "hailo8l")

    def test_detect_hailo_arch_hailo8(self):
        fake_output = "Device Architecture: HAILO8\n"
        mock_result = MagicMock(returncode=0, stdout=fake_output, stderr="")
        with patch("subprocess.run", return_value=mock_result), patch(
            "frigate.detectors.plugins.hailo.find_tool", return_value="hailortcli"
        ):
            arch = hailo.detect_hailo_arch()
            self.assertEqual(arch, "hailo8")

    def test_detect_hailo_arch_failure(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="Device not found")
        with patch("subprocess.run", return_value=mock_result), patch(
            "frigate.detectors.plugins.hailo.find_tool", return_value="hailortcli"
        ):
            arch = hailo.detect_hailo_arch()
            self.assertIsNone(arch)

    def test_extract_model_name(self):
        with patch.object(hailo, "ARCH", "hailo10h"):
            self.assertEqual(hailo.HailoDetector.extract_model_name(), hailo.H10_DEFAULT_MODEL)

        with patch.object(hailo, "ARCH", "hailo8"):
            self.assertEqual(hailo.HailoDetector.extract_model_name(), hailo.H8_DEFAULT_MODEL)

        with patch.object(hailo, "ARCH", "hailo8l"):
            self.assertEqual(hailo.HailoDetector.extract_model_name(), hailo.H8L_DEFAULT_MODEL)

        self.assertEqual(
            hailo.HailoDetector.extract_model_name(path="/models/custom_h10.hef"),
            "custom_h10.hef",
        )
        self.assertEqual(
            hailo.HailoDetector.extract_model_name(url="https://example.com/custom_model.hef"),
            "custom_model.hef",
        )

    def test_check_and_prepare_downloads_h10_default_model(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            detector = MagicMock(spec=hailo.HailoDetector)
            detector.cache_dir = tmp_dir
            detector.model_path = None
            detector.url = None
            detector.extract_model_name = hailo.HailoDetector.extract_model_name
            detector.download_model = MagicMock()

            with patch.object(hailo, "ARCH", "hailo10h"):
                hailo.HailoDetector.check_and_prepare(detector)
                detector.download_model.assert_called_once_with(
                    hailo.H10_DEFAULT_URL,
                    os.path.join(tmp_dir, hailo.H10_DEFAULT_MODEL),
                )

    def test_hailo_async_inference_sets_shared_group(self):
        fake_params = MagicMock()
        fake_params.group_id = None
        fake_vdevice_cls = MagicMock()
        fake_vdevice_cls.create_params.return_value = fake_params

        fake_hef_cls = MagicMock()
        fake_scheduling = MagicMock()

        modules = {
            "hailo_platform": MagicMock(
                HEF=fake_hef_cls,
                FormatType=MagicMock(),
                HailoSchedulingAlgorithm=fake_scheduling,
                VDevice=fake_vdevice_cls,
            )
        }
        with patch.dict("sys.modules", modules):
            input_store = MagicMock()
            output_store = MagicMock()
            hailo.HailoAsyncInference(
                hef_path="dummy.hef",
                input_store=input_store,
                output_store=output_store,
            )
            self.assertEqual(fake_params.group_id, "SHARED")

