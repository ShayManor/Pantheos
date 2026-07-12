from app import metrics


class FakeContainer:
    def __init__(self, cid, up, status, cpu_n=10, image="x/y:tag"):
        self.id = cid
        self.up = up
        self.status = status
        self.cpu_n = cpu_n
        self.image = image


def test_seed_of_str_and_int():
    assert metrics._seed_of("abc") == ord("a") + ord("b") + ord("c")
    assert metrics._seed_of(5) == 5


def test_spark_deterministic_and_nonnegative():
    a = metrics.spark(100, 14, 0.25, 3)
    b = metrics.spark(100, 14, 0.25, 3)
    assert a == b
    assert len(a) == 14
    assert all(p["v"] >= 0 for p in a)


def test_container_metrics_online_and_off():
    on = metrics.container_metrics(FakeContainer("gh-stats-api", "AOS", "flt", 38))
    assert on["off"] is False and len(on["series"]) == 20
    off = metrics.container_metrics(FakeContainer("merlin-edge", "LOS", "los", 0))
    assert off["off"] is True


def test_usage_and_error_series():
    assert len(metrics.usage_series()) == 14
    e = metrics.error_series()
    assert len(e) == 14
    assert e[11]["v"] >= 5  # i > 10 branch adds 5


def test_container_logs_all_statuses():
    los = metrics.container_logs(FakeContainer("merlin-edge", "LOS", "los"))
    assert any(l["lvl"] == "err" for l in los)
    flt = metrics.container_logs(FakeContainer("gh-stats-api", "AOS", "flt"))
    assert any("500" in l["msg"] for l in flt)
    cau = metrics.container_logs(FakeContainer("gpufindr-scraper", "AOS", "cau"))
    assert any("selector drift" in l["msg"] for l in cau)
    go = metrics.container_logs(FakeContainer("gh-stats-web", "AOS", "go"))
    assert any("healthz" in l["msg"] for l in go)
    # deterministic
    assert metrics.container_logs(FakeContainer("x", "AOS", "go")) == \
        metrics.container_logs(FakeContainer("x", "AOS", "go"))


def test_log_timestamps_rollover():
    ts = metrics.log_timestamps(7, 100)
    assert len(ts) == 100
    assert any(int(t[:2]) > 14 for t in ts)  # minutes rolled over into a new hour
