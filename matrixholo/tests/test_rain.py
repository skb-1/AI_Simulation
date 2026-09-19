"""Unit tests for digital rain simulation."""

from matrixholo.rain import DigitalRain, RainDrop
from matrixholo.zbuffer import ZBuffer


def test_raindrop_update():
    drop = RainDrop(col=5, max_height=20)
    old_y = drop.y
    drop.update(0.1, max_height=20)
    assert drop.y > old_y


def test_digital_rain_render():
    zbuf = ZBuffer(30, 20)
    rain = DigitalRain(30, 20, density=0.8, enabled=True)
    rain.update(0.1)
    rain.render(zbuf)
    # Check that some cells contain characters
    char_count = sum(1 for c in zbuf.char if c != " ")
    assert char_count > 0
