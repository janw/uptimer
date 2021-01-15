import re
from itertools import islice
from typing import Iterable

from structlog import get_logger

from uptimer.core import settings

logger = get_logger()


RE_WORKER_ID = re.compile(r"(\d+)")


class DistributeWorkMixin:
    distributed_workers_enabled = False
    distributed_workers_total = 1
    distributed_workers_index = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.as_bool("DISTRIBUTED_WORKERS_ENABLED") is False:
            return
        self.distributed_workers_enabled = True

        if "DISTRIBUTED_WORKERS_TOTAL" not in settings:
            raise ValueError("DISTRIBUTED_WORKERS_TOTAL must be set")
        try:
            self.distributed_workers_total = int(settings.DISTRIBUTED_WORKERS_TOTAL)
        except ValueError:
            raise ValueError("DISTRIBUTED_WORKERS_TOTAL must be an integer")

        if "DISTRIBUTED_WORKERS_INDEX" not in settings:
            raise ValueError("DISTRIBUTED_WORKERS_INDEX must be set")

        # Use regex here to find the first integer within the INDEX variable to allow
        # detection of k8s StatefulSet members' indices (formatted as
        # `mystatefulset-123`)
        potential_index = re.findall(r"(\d+)", settings.DISTRIBUTED_WORKERS_INDEX)
        if len(potential_index) == 0:
            raise ValueError("DISTRIBUTED_WORKERS_INDEX must be parseable to an index")
        self.distributed_workers_index = int(potential_index[0])

    def distribute_data(self, data: Iterable):
        yield from islice(
            data,
            self.distributed_workers_index,
            None,
            self.distributed_workers_total,
        )
