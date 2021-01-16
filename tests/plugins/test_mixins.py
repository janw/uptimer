import pytest

from uptimer.plugins.mixins import DistributeWorkMixin


def test_distributed_worker_init(conf_override):
    d = DistributeWorkMixin()
    assert d.distributed_workers_enabled is False

    conf_override("DISTRIBUTED_WORKERS_ENABLED", "true")

    with pytest.raises(ValueError):
        d = DistributeWorkMixin()

    conf_override("DISTRIBUTED_WORKERS_TOTAL", "ninetimes")

    with pytest.raises(ValueError):
        d = DistributeWorkMixin()

    conf_override("DISTRIBUTED_WORKERS_TOTAL", "3")

    with pytest.raises(ValueError):
        d = DistributeWorkMixin()

    conf_override("DISTRIBUTED_WORKERS_INDEX", "noindex")

    with pytest.raises(ValueError):
        d = DistributeWorkMixin()

    # index must be zero-indexed within range of worker total count
    conf_override("DISTRIBUTED_WORKERS_INDEX", "node-3")

    with pytest.raises(ValueError):
        d = DistributeWorkMixin()

    conf_override("DISTRIBUTED_WORKERS_INDEX", "node-1")

    d = DistributeWorkMixin()

    assert d.distributed_workers_enabled is True
    assert d.distributed_workers_total == 3
    assert d.distributed_workers_index == 1


def test_distributed_worker_init_native_Values(conf_override):
    conf_override("DISTRIBUTED_WORKERS_ENABLED", True)
    conf_override("DISTRIBUTED_WORKERS_TOTAL", 7)
    conf_override("DISTRIBUTED_WORKERS_INDEX", 6)

    d = DistributeWorkMixin()

    assert d.distributed_workers_enabled is True
    assert d.distributed_workers_total == 7
    assert d.distributed_workers_index == 6


@pytest.mark.parametrize(
    "input_val,worker_total,worker_index,expected",
    [
        ([1, 2, 3, 4, 5, 6], 3, 0, [1, 4]),
        ([1, 2, 3, 4, 5, 6], 3, 1, [2, 5]),
        ([1, 2, 3, 4, 5, 6], 3, 2, [3, 6]),
        ([1, 2, 3], 3, 1, [2]),
        ([(1, 2), (3, 4)], 3, 0, [(1, 2)]),
    ],
)
def test_distribute_data(
    input_val, worker_total, worker_index, expected, conf_override
):
    d = DistributeWorkMixin()
    d.distributed_workers_enabled = True
    d.distributed_workers_total = worker_total
    d.distributed_workers_index = worker_index

    assert list(d.distribute_data(input_val)) == expected
