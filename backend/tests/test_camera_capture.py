"""Camera startup regression tests using in-memory frames and fake devices only."""

import sys
from types import SimpleNamespace

import pytest

from scripts import webcam_gesture_client as webcam


class CaptureError(Exception):
    pass


class FakeCapture:
    def __init__(self, reads=(), *, opened=True, events=None, name="capture"):
        self.reads = iter(reads)
        self.opened = opened
        self.events = events if events is not None else []
        self.name = name
        self.read_count = 0
        self.release_count = 0

    def isOpened(self):
        return self.opened

    def read(self):
        self.read_count += 1
        result = next(self.reads, (False, None))
        if isinstance(result, Exception):
            raise result
        return result

    def release(self):
        self.release_count += 1
        self.events.append(("release", self.name))


@pytest.fixture
def frame():
    np = pytest.importorskip("numpy")
    return np.zeros((48, 64, 3), dtype=np.uint8)


@pytest.fixture(autouse=True)
def no_warmup_delay(monkeypatch):
    monkeypatch.setattr(webcam.time, "sleep", lambda _: None)


def fake_cv(captures, events=None):
    events = events if events is not None else []

    def create(index, backend=0):
        events.append(("open", index, backend))
        capture = captures[(index, backend)]
        if isinstance(capture, Exception):
            raise capture
        return capture

    return SimpleNamespace(VideoCapture=create, CAP_DSHOW=700, CAP_MSMF=1400, error=CaptureError)


def test_windows_falls_back_when_open_device_never_delivers_frames(monkeypatch, frame):
    monkeypatch.setattr(webcam.platform, "system", lambda: "Windows")
    events = []
    dshow = FakeCapture(events=events, name="dshow")
    msmf = FakeCapture([(True, frame)], events=events, name="msmf")
    capture, first, index, backend = webcam.open_camera(fake_cv({(2, 700): dshow, (2, 1400): msmf}, events), 2)

    assert (capture, index, backend) == (msmf, 2, "msmf")
    assert first is frame
    assert dshow.read_count == webcam.CAMERA_WARMUP_READS
    assert dshow.release_count == 1 and msmf.release_count == 0
    assert events == [("open", 2, 700), ("release", "dshow"), ("open", 2, 1400)]


def test_default_does_not_select_another_device_after_failure(monkeypatch, frame):
    monkeypatch.setattr(webcam.platform, "system", lambda: "Windows")
    events = []
    zero_dshow = FakeCapture(opened=False, events=events, name="zero-dshow")
    zero_msmf = FakeCapture(events=events, name="zero-msmf")
    one_dshow = FakeCapture([(True, frame)], events=events, name="one-dshow")
    with pytest.raises(webcam.CameraOpenError):
        webcam.open_camera(fake_cv({
            (0, 700): zero_dshow, (0, 1400): zero_msmf, (1, 700): one_dshow,
        }, events))

    assert one_dshow.read_count == 0
    assert events == [
        ("open", 0, 700), ("release", "zero-dshow"),
        ("open", 0, 1400), ("release", "zero-msmf"),
    ]


def test_warmup_ignores_missing_and_empty_frames(monkeypatch, frame):
    np = pytest.importorskip("numpy")
    monkeypatch.setattr(webcam.platform, "system", lambda: "Linux")
    device = FakeCapture([(False, None), (True, None), (True, np.empty((0, 64, 3))), (True, frame)])
    capture, first, index, backend = webcam.open_camera(fake_cv({(0, 0): device}), 0)

    assert (capture, index, backend) == (device, 0, "default")
    assert first is frame and device.read_count == 4
    assert device.release_count == 0


def test_explicit_backend_and_index_do_not_probe_other_devices(frame):
    events = []
    device = FakeCapture([(True, frame)])
    capture, first, index, backend = webcam.open_camera(fake_cv({(3, 1400): device}, events), 3, "msmf")
    assert (capture, index, backend) == (device, 3, "msmf")
    assert first is frame and events == [("open", 3, 1400)]


def test_all_candidates_report_failures_and_release(monkeypatch):
    monkeypatch.setattr(webcam.platform, "system", lambda: "Windows")
    dshow = FakeCapture(opened=False)
    msmf = FakeCapture([CaptureError("driver read failed")])
    with pytest.raises(webcam.CameraOpenError) as error:
        webcam.open_camera(fake_cv({(0, 700): dshow, (0, 1400): msmf}), 0)
    assert "camera 0" in str(error.value)
    assert "dshow: device could not be opened" in str(error.value)
    assert "msmf: capture failed (driver read failed)" in str(error.value)
    assert dshow.release_count == msmf.release_count == 1


def test_constructor_error_can_fall_back(monkeypatch, frame):
    monkeypatch.setattr(webcam.platform, "system", lambda: "Windows")
    device = FakeCapture([(True, frame)])
    assert webcam.open_camera(fake_cv({(0, 700): CaptureError("open failed"), (0, 1400): device}), 0)[0] is device


def test_check_camera_needs_no_api_hook_or_gui(monkeypatch, capsys, frame):
    monkeypatch.setattr(webcam.platform, "system", lambda: "Linux")
    device = FakeCapture([(True, frame)])
    # This fake deliberately has no GUI or image-processing functions.
    monkeypatch.setitem(sys.modules, "cv2", fake_cv({(2, 0): device}))
    monkeypatch.setattr(sys, "argv", ["webcam", "--check-camera", "--camera", "2"])
    monkeypatch.setattr(webcam, "post_json", lambda *_: pytest.fail("camera check must not call the API"))
    monkeypatch.setattr(webcam, "make_input_observer", lambda: pytest.fail("camera check must not install a hook"))

    assert webcam.main() == 0
    assert device.read_count == device.release_count == 1
    assert "Camera frame received: index=2, backend=default, frame=64x48" in capsys.readouterr().out


def test_check_camera_failure_returns_error_without_api(monkeypatch, capsys):
    pytest.importorskip("numpy")
    device = FakeCapture(opened=False)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv({(0, 0): device}))
    monkeypatch.setattr(sys, "argv", ["webcam", "--check-camera", "--camera", "0", "--camera-backend", "default"])
    monkeypatch.setattr(webcam, "post_json", lambda *_: pytest.fail("camera check must not call the API"))

    assert webcam.main() == 1
    assert device.release_count == 1
    assert "camera 0: default: device could not be opened" in capsys.readouterr().err


def test_preview_uses_first_verified_frame_and_cleans_up(monkeypatch, frame):
    device = FakeCapture([(True, frame)])
    cv = fake_cv({(0, 0): device})
    displayed = []
    destroyed = []
    cv.createBackgroundSubtractorMOG2 = lambda **_: None
    cv.flip = lambda image, _: image
    cv.cvtColor = lambda image, _: image[:, :, 0]
    cv.GaussianBlur = lambda image, *_: image
    cv.rectangle = lambda *_: None
    cv.putText = lambda *_: None
    cv.imshow = lambda _, image: displayed.append(image)
    cv.waitKey = lambda _: ord("q")
    cv.destroyAllWindows = lambda: destroyed.append(True)
    cv.COLOR_BGR2GRAY = cv.FONT_HERSHEY_SIMPLEX = 0
    monkeypatch.setitem(sys.modules, "cv2", cv)
    monkeypatch.setattr(sys, "argv", ["webcam", "--input-mode", "labels", "--activity", "music",
                                     "--camera", "0", "--camera-backend", "default"])
    monkeypatch.setattr(webcam, "post_json", lambda *_: {})

    assert webcam.main() == 0
    assert len(displayed) == 1 and displayed[0] is frame
    assert device.read_count == device.release_count == 1
    assert destroyed == [True]


def test_initialization_exception_releases_camera(monkeypatch, frame):
    device = FakeCapture([(True, frame)])
    cv = fake_cv({(0, 0): device})
    def fail_initialization(**_):
        raise CaptureError("background setup failed")
    cv.createBackgroundSubtractorMOG2 = fail_initialization
    monkeypatch.setitem(sys.modules, "cv2", cv)
    monkeypatch.setattr(sys, "argv", ["webcam", "--input-mode", "labels", "--activity", "music",
                                     "--camera", "0", "--camera-backend", "default"])

    assert webcam.main() == 1
    assert device.release_count == 1


def test_negative_camera_index_is_rejected(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["webcam", "--check-camera", "--camera", "-1"])
    with pytest.raises(SystemExit) as error:
        webcam.main()
    assert error.value.code == 2
