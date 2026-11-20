"""Check map extension across a failed batch, including duplicate keys in both scopes."""
import pytest

from ztes.model.epistemic import bind
from ztes.model.view import Record


@pytest.mark.parametrize("values,exception", [
    ([1, 2, 0], ZeroDivisionError),
    ([1, 2, 1], ValueError),   # duplicate in the committed prefix
    ([1, 2, 2], ValueError),   # duplicate in the new batch
])
def test_failed_map_extension_matches_fresh_index(values, exception):
    events = [{"coord": {"kind": "exec", "abstraction": "t"}, "payload": v} for v in values]
    record = Record.of(events)
    binding = {"from": "t", "select": "map", "type": "integer", "key": "x", "value": "10 // x"}

    def mapping(prefix):
        return bind(prefix, "m", binding)

    previous = mapping(record[:1])
    with pytest.raises(exception) as fresh_error:
        mapping(Record.of(events))
    for _ in range(2):
        with pytest.raises(exception) as cached_error:
            mapping(record)
        assert str(cached_error.value) == str(fresh_error.value)
        assert dict(previous) == {1: 10}
        assert dict(mapping(record[:2])) == dict(mapping(Record.of(events[:2]))) == {1: 10, 2: 5}
