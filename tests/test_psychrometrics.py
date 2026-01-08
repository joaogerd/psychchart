import numpy as np
from psychchart.psychrometrics import Psychrometrics


def test_saturation_pressure_monotonic():
    T = np.array([0.0, 10.0, 20.0, 30.0])
    p = Psychrometrics.saturation_pressure(T)
    assert np.all(np.diff(p) > 0)


def test_humidity_ratio_increases_with_rh():
    T = 25.0
    W1 = Psychrometrics.humidity_ratio(T, 0.3)
    W2 = Psychrometrics.humidity_ratio(T, 0.6)
    assert W2 > W1


def test_enthalpy_increases_with_temperature():
    T1, T2 = 20.0, 30.0
    W = 0.01
    h1 = Psychrometrics.enthalpy(T1, W)
    h2 = Psychrometrics.enthalpy(T2, W)
    assert h2 > h1


def test_specific_volume_positive():
    v = Psychrometrics.specific_volume(25.0, 0.01)
    assert v > 0.0


def test_relative_humidity_inverse():
    T = 25.0
    RH = 0.5
    W = Psychrometrics.humidity_ratio(T, RH)
    RH_back = Psychrometrics.relative_humidity_from_W(T, W)
    assert abs(RH - RH_back) < 1e-3

