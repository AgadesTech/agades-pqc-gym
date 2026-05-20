from __future__ import annotations

from agades_pqc_gym.evaluators.lattice_estimator_sage_worker import _json_safe


class _CostLike:
    def __init__(self) -> None:
        self._items = {
            "rop": _FloatLike(39.25),
            "red": _FloatLike(38.5),
            "beta": _FloatLike(40.0),
            "tag": "usvp",
        }

    def keys(self) -> list[str]:
        return list(self._items)

    def __getitem__(self, key: str) -> object:
        return self._items[key]


class _FloatLike:
    def __init__(self, value: float) -> None:
        self._value = value

    def __float__(self) -> float:
        return self._value


def test_json_safe_serializes_mapping_like_lattice_estimator_costs() -> None:
    assert _json_safe({"usvp": _CostLike()}) == {
        "usvp": {
            "rop": 39.25,
            "red": 38.5,
            "beta": 40.0,
            "tag": "usvp",
        }
    }
