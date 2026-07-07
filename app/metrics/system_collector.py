import asyncio
import time

import psutil

from .system_metrics import (
    process_cpu_seconds_total,
    process_resident_memory_bytes,
    process_virtual_memory_bytes,
    process_start_time_seconds,
)


_process: psutil.Process | None = None
_task: asyncio.Task | None = None


def _get_process() -> psutil.Process:
    global _process
    if _process is None:
        _process = psutil.Process()
    return _process


async def _collect_loop() -> None:
    process = _get_process()
    process_start_time_seconds.set(process.create_time())

    while True:
        try:
            with process.oneshot():
                cpu_seconds = process.cpu_times()
                process_cpu_seconds_total.inc(cpu_seconds.user + cpu_seconds.system)

                mem_info = process.memory_info()
                process_resident_memory_bytes.set(mem_info.rss)
                process_virtual_memory_bytes.set(mem_info.vms)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        await asyncio.sleep(15)


def start_system_metrics() -> None:
    global _task
    if _task is not None:
        return

    _task = asyncio.create_task(_collect_loop(), name="SystemMetricsCollector")


def stop_system_metrics() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
