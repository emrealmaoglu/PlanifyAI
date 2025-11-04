"""
Performance Profiling Utilities
================================
Utilities for profiling optimization performance.

Functions:
    profile_optimization: Decorator for profiling entire optimization
    profile_function: Decorator for profiling individual functions
    analyze_profile: Print profiling statistics

Created: 2025-11-04
"""
import cProfile
import functools
import io
import logging
import pstats
from typing import Callable

logger = logging.getLogger(__name__)


def profile_optimization(func: Callable) -> Callable:
    """
    Decorator to profile entire optimization function.

    Saves profile to outputs/ directory and prints top functions.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with profiling

    Example:
        >>> @profile_optimization
        ... def optimize():
        ...     # ... optimization code ...
        ...     pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()

            # Save profile
            import os

            os.makedirs("outputs", exist_ok=True)
            profile_file = f"outputs/{func.__name__}_profile.prof"
            profiler.dump_stats(profile_file)
            logger.info(f"Profile saved to {profile_file}")

            # Print statistics
            analyze_profile(profiler, top_n=20)

        return result

    return wrapper


def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile individual function calls.

    Logs execution time for each call.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with profiling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()

            # Log summary
            s = io.StringIO()
            stats = pstats.Stats(profiler, stream=s)
            stats.sort_stats("cumulative")
            stats.print_stats(5)  # Top 5 functions
            logger.debug(f"{func.__name__} profile:\n{s.getvalue()}")

        return result

    return wrapper


def analyze_profile(
    profiler: cProfile.Profile, top_n: int = 20, sort_by: str = "cumulative"
) -> None:
    """
    Analyze and print profiling statistics.

    Args:
        profiler: cProfile.Profile instance
        top_n: Number of top functions to print
        sort_by: Sort key ('cumulative', 'tottime', 'calls')
    """
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats(sort_by)
    stats.print_stats(top_n)

    logger.info(f"Profile analysis (top {top_n} functions by {sort_by}):")
    logger.info(s.getvalue())


def load_and_analyze_profile(profile_file: str, top_n: int = 20) -> None:
    """
    Load profile from file and analyze it.

    Args:
        profile_file: Path to .prof file
        top_n: Number of top functions to print
    """
    profiler = cProfile.Profile()
    profiler.load_stats(profile_file)
    analyze_profile(profiler, top_n=top_n)
