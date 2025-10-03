from passive_radar.tools import utils

def test_timer_context():
    with utils.timer("dummy"):
        x = 1 + 1
    assert x == 2
