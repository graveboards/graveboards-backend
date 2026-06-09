"""
Test performance benchmarking utilities.

Provides pytest hooks and fixtures for tracking test execution time.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any
from functools import wraps
import pytest
import asyncio

from datetime import datetime
from collections import defaultdict

# Performance registry
_perf_registry = defaultdict(list)


def track_performance(name: str | None = None):
    """Decorator to track test execution performance.
    
    Usage:
        @track_performance("custom_name")
        def test_something():
            ...
    """
    def decorator(func):
        test_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.perf_counter() - start) * 1000
                _perf_registry[test_name].append({
                    'duration_ms': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'passed': True,
                })
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.perf_counter() - start) * 1000
                _perf_registry[test_name].append({
                    'duration_ms': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'passed': True,
                })
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Pytest hook to track test execution time."""
    test_name = item.nodeid
    start = time.perf_counter()
    
    try:
        yield
        passed = True
    except Exception:
        passed = False
        raise
    finally:
        duration = (time.perf_counter() - start) * 1000
        _perf_registry[test_name].append({
            'duration_ms': duration,
            'timestamp': datetime.utcnow().isoformat(),
            'passed': passed,
        })


def get_slow_tests(threshold_ms: float = 100.0) -> list[dict]:
    """Get list of tests exceeding time threshold."""
    slow = []
    for test_name, runs in _perf_registry.items():
        for run in runs:
            if run['duration_ms'] > threshold_ms:
                slow.append({
                    'test': test_name,
                    'duration_ms': run['duration_ms'],
                    'passed': run['passed'],
                })
    return sorted(slow, key=lambda x: x['duration_ms'], reverse=True)


def print_benchmark_report():
    """Print benchmark report to console."""
    if not _perf_registry:
        print("No benchmark data collected.")
        return
    
    print("\n" + "=" * 80)
    print("TEST PERFORMANCE BENCHMARK REPORT")
    print("=" * 80)
    
    for test_name, runs in sorted(_perf_registry.items(), 
                                   key=lambda x: sum(r['duration_ms'] for r in x[1]), 
                                   reverse=True):
        durations = [r['duration_ms'] for r in runs]
        total = sum(durations)
        avg = total / len(durations)
        min_val = min(durations)
        max_val = max(durations)
        passed = sum(1 for r in runs if r['passed'])
        
        print(f"\n{test_name}")
        print(f"  Runs: {len(runs)} | Total: {total:.2f}ms | Avg: {avg:.2f}ms")
        print(f"  Min: {min_val:.2f}ms | Max: {max_val:.2f}ms | Passed: {passed}/{len(runs)}")


def save_benchmark_results(path: Path, data: dict):
    """Save benchmark results to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_benchmark_results(path: Path) -> dict:
    """Load benchmark results from JSON."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


__all__ = [
    'track_performance',
    'get_slow_tests',
    'print_benchmark_report',
    'save_benchmark_results',
    'load_benchmark_results',
]