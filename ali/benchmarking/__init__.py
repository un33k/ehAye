"""Benchmarking module for ehAye - performance testing and metrics collection."""

# Core benchmark functionality
from .runner import (
    BenchmarkRunner,
    benchmark_runner,
    benchmark_model,
    compare_models,
)

# Metrics collection and calculation
from .metrics import (
    BenchmarkResult,
    ModelBenchmarkSummary,
    MetricsCollector,
    metrics_collector,
    collect_benchmark_metrics,
    calculate_benchmark_summary,
)

# Rich formatted reporting
from .reports import (
    BenchmarkReporter,
    benchmark_reporter,
    print_benchmark_report,
    print_comparison_report,
    export_results_to_json,
)

# System resource monitoring
from .system import (
    SystemMonitor,
    system_monitor,
    check_system_requirements,
    get_system_info,
    validate_benchmark_environment,
)

__all__ = [
    # Core benchmark functionality
    "BenchmarkRunner",
    "benchmark_runner",
    "benchmark_model", 
    "compare_models",
    
    # Metrics collection and calculation
    "BenchmarkResult",
    "ModelBenchmarkSummary",
    "MetricsCollector",
    "metrics_collector",
    "collect_benchmark_metrics",
    "calculate_benchmark_summary",
    
    # Rich formatted reporting
    "BenchmarkReporter",
    "benchmark_reporter",
    "print_benchmark_report",
    "print_comparison_report",
    "export_results_to_json",
    
    # System resource monitoring
    "SystemMonitor",
    "system_monitor",
    "check_system_requirements",
    "get_system_info",
    "validate_benchmark_environment",
]