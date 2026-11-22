from types import SimpleNamespace

from s_audio_pin.audio.monitor import AudioMonitor
from s_audio_pin.models.audio import AudioSource


class FakePeakWorker:
    def __init__(self, is_app: bool, target: str, sink_id=None):
        self.is_app = is_app
        self.target = target
        self.sink_id = sink_id
        self.peak = 0.25
        self.alive = True
        self.stopped = False

    def is_alive(self) -> bool:
        return self.alive

    def stop(self):
        self.stopped = True
        self.alive = False


def _make_sink_input(index: int, sink: int, app_name: str, binary: str, pid: int = 1000):
    return SimpleNamespace(
        index=index,
        sink=sink,
        channel_count=2,
        sample_spec=SimpleNamespace(rate=48000),
        volume=SimpleNamespace(value_flat=1.0),
        mute=False,
        proplist={
            "application.name": app_name,
            "application.process.binary": binary,
            "application.process.id": str(pid),
        },
    )


def _make_source(index: int, name: str, desc: str, bus: str = "pci", monitor_of=None):
    return SimpleNamespace(
        index=index,
        name=name,
        description=desc,
        monitor_of_sink=monitor_of,
        port_active=None,
        channel_count=1,
        sample_spec=SimpleNamespace(rate=48000),
        volume=SimpleNamespace(value_flat=1.0),
        mute=False,
        proplist={"device.bus": bus},
    )


def test_audio_source_creation():
    src = AudioSource(
        id="sink_input:100",
        type="app",
        index=100,
        name="VLC Media Player",
        process_name="vlc",
        pid=1234,
        volume=1.0,
        is_muted=False,
        peak_level=0.5,
    )
    d = src.to_dict()
    assert d["id"] == "sink_input:100"
    assert d["name"] == "VLC Media Player"
    assert d["peak_level"] == 0.5
    assert d["type"] == "app"


def test_monitor_peak_decay():
    monitor = AudioMonitor()
    decayed = monitor._apply_decay(prev_peak=0.8, new_peak=0.2)
    assert 0.2 < decayed < 0.8
    rising = monitor._apply_decay(prev_peak=0.2, new_peak=0.9)
    assert rising == 0.9


def test_monitor_does_not_spawn_worker_for_unarmed_or_bt_mic():
    monitor = AudioMonitor()
    created = []

    def fake_create(is_app, target, sink_id=None):
        w = FakePeakWorker(is_app, target, sink_id)
        created.append(w)
        return w

    monitor._create_worker = fake_create

    wired_mic = _make_source(10, "alsa_input.pci.stereo", "Internal Mic", bus="pci")
    bt_mic = _make_source(20, "bluez_input.11_22_33_44_55_66.0", "BT Headset", bus="bluetooth")
    mon_src = _make_source(30, "alsa_output.pci.monitor", "Monitor", monitor_of=1)

    # Even if BT mic is armed, never open a peak worker on it (prevents A2DP -> HFP switch)
    monitor.set_monitored_mics(["source:20"])
    monitor._process_snapshot([], [wired_mic, bt_mic, mon_src])

    assert len(created) == 0
    assert len(monitor._workers) == 0
    sources = monitor.get_sources()
    assert len(sources["mics"]) == 2
    assert any(m["is_bluetooth"] for m in sources["mics"])


def test_monitor_spawns_worker_for_armed_wired_mic_and_stops_when_unarmed():
    monitor = AudioMonitor()
    created = []
    monitor._create_worker = lambda is_app, target, sink_id=None: (
        created.append(FakePeakWorker(is_app, target, sink_id)) or created[-1]
    )

    wired_mic = _make_source(10, "alsa_input.pci.stereo", "Internal Mic", bus="pci")

    monitor.set_monitored_mics(["source:10"])
    monitor._process_snapshot([], [wired_mic])
    assert len(created) == 1
    assert "mic:alsa_input.pci.stereo" in monitor._workers

    monitor.set_monitored_mics([])
    assert created[0].stopped is True
    assert "mic:alsa_input.pci.stereo" not in monitor._workers


def test_monitor_restarts_dead_and_sink_changed_app_workers():
    monitor = AudioMonitor()
    created = []
    monitor._create_worker = lambda is_app, target, sink_id=None: (
        created.append(FakePeakWorker(is_app, target, sink_id)) or created[-1]
    )

    si = _make_sink_input(55, sink=1, app_name="Firefox", binary="firefox", pid=999)
    monitor._process_snapshot([si], [])
    assert len(created) == 1
    w1 = created[0]
    assert w1.sink_id == 1

    # Simulate worker crash
    w1.alive = False
    monitor._process_snapshot([si], [])
    assert w1.stopped is True
    assert len(created) == 2
    w2 = created[1]

    # Simulate Bluetooth sink switch (sink 1 -> sink 4)
    si_moved = _make_sink_input(55, sink=4, app_name="Firefox", binary="firefox", pid=999)
    monitor._process_snapshot([si_moved], [])
    assert w2.stopped is True
    assert len(created) == 3
    assert created[2].sink_id == 4


def test_get_live_streams_for_source_app_and_bt_mic():
    monitor = AudioMonitor()
    monitor._create_worker = lambda is_app, target, sink_id=None: FakePeakWorker(is_app, target, sink_id)

    si = _make_sink_input(88, sink=3, app_name="Discord", binary="discord", pid=4321)
    bt_mic = _make_source(
        22,
        "bluez_input.AA_BB_CC_DD_EE_FF.headset-head-unit",
        "BT Headset",
        bus="bluetooth",
    )
    monitor._process_snapshot([si], [bt_mic])

    # App matched even if stream index rotated
    app_src = AudioSource(
        id="app:proc_discord",
        type="app",
        index=77,
        name="Discord",
        process_name="discord",
        pid=4321,
    )
    app_res = monitor.get_live_streams_for_source(app_src)
    assert app_res["found"] is True
    assert app_res["streams"] == [(88, 3)]

    # BT mic matched across profile suffix / index change by BT MAC identity
    bt_src = AudioSource(
        id="source:99",
        type="mic",
        index=99,
        name="Bluetooth: BT Headset",
        device_name="bluez_input.AA_BB_CC_DD_EE_FF.0",
        is_bluetooth=True,
    )
    mic_res = monitor.get_live_streams_for_source(bt_src)
    assert mic_res["found"] is True
    assert mic_res["device_name"] == "bluez_input.AA_BB_CC_DD_EE_FF.headset-head-unit"
