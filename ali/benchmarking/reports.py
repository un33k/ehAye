"""Benchmark reporting and visualization."""

from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..logging import get_logger
from .metrics import ModelBenchmarkSummary

logger = get_logger("benchmarking.reports")


class BenchmarkReporter:
    """Generates formatted benchmark reports."""
    
    def __init__(self):
        self.console = Console()
    
    def print_single_model_report(self, summary: ModelBenchmarkSummary) -> None:
        """Print detailed report for a single model."""
        self.console.print(f"\n📊 Benchmark Results for {summary.model_name}")
        self.console.print("=" * 60)
        
        # System info
        sys_info = summary.system_info
        self.console.print(Panel(
            f"🖥️  Chip: {sys_info.get('chip', 'Unknown')}\n"
            f"💾 Memory: {sys_info.get('total_memory_gb', 0)}GB total, "
            f"{sys_info.get('available_memory_gb', 0)}GB available\n"
            f"🧠 CPU: {sys_info.get('cpu_count', 0)} cores "
            f"({sys_info.get('cpu_count_logical', 0)} logical)\n"
            f"🎮 GPU: {sys_info.get('gpu_memory_mb', 'N/A')}MB allocated",
            title="System Information",
            border_style="blue"
        ))
        
        # Performance metrics
        self.console.print(Panel(
            f"⏱️  Model load time: {summary.load_time:.2f}s\n"
            f"💾 Model memory usage: {summary.model_memory_mb:.1f}MB\n"
            f"📈 Peak memory usage: {summary.peak_memory_mb:.1f}MB\n"
            f"✅ Successful runs: {summary.successful_runs}/{summary.total_runs}",
            title="Loading & Memory",
            border_style="green"
        ))
        
        # Generation performance
        performance_color = self._get_performance_color(summary.avg_tokens_per_second)
        self.console.print(Panel(
            f"⚡ Average: {summary.avg_tokens_per_second:.1f} tokens/sec\n"
            f"🚀 Maximum: {summary.max_tokens_per_second:.1f} tokens/sec\n"
            f"🐌 Minimum: {summary.min_tokens_per_second:.1f} tokens/sec\n"
            f"⏳ Avg time: {summary.avg_generation_time:.2f}s",
            title="Generation Performance",
            border_style=performance_color
        ))
        
        # Performance rating
        rating = self._get_performance_rating(summary.avg_tokens_per_second)
        rating_color = self._get_performance_color(summary.avg_tokens_per_second)
        
        self.console.print(Panel(
            f"🎯 {rating}\n"
            f"📊 Efficiency: {self._calculate_efficiency(summary):.2f} MB per token/sec",
            title="Overall Rating",
            border_style=rating_color
        ))
    
    def print_comparison_report(self, summaries: List[ModelBenchmarkSummary]) -> None:
        """Print comparison report for multiple models."""
        if not summaries:
            self.console.print("❌ No benchmark results to display")
            return
        
        self.console.print(f"\n🏆 Model Comparison Results")
        self.console.print("=" * 80)
        
        # Create comparison table
        table = Table()
        table.add_column("Rank", style="bold blue", width=4)
        table.add_column("Model", style="bold", width=35)
        table.add_column("Tokens/sec", justify="right", width=12)
        table.add_column("Memory", justify="right", width=10)
        table.add_column("Load Time", justify="right", width=10)
        table.add_column("Rating", justify="center", width=8)
        
        for i, summary in enumerate(summaries):
            model_name = summary.model_name[:30] + "..." if len(summary.model_name) > 30 else summary.model_name
            tokens_per_sec = f"{summary.avg_tokens_per_second:.1f}"
            memory = f"{summary.model_memory_mb:.0f}MB"
            load_time = f"{summary.load_time:.1f}s"
            rating = self._get_performance_emoji(summary.avg_tokens_per_second)
            
            # Color code based on performance
            if i == 0:  # Best performer
                style = "bold green"
            elif summary.avg_tokens_per_second > 50:
                style = "green"
            elif summary.avg_tokens_per_second > 20:
                style = "yellow"
            else:
                style = "red"
            
            table.add_row(
                str(i + 1),
                model_name,
                tokens_per_sec,
                memory,
                load_time,
                rating,
                style=style
            )
        
        self.console.print(table)
        
        # Recommendations
        if summaries:
            self._print_recommendations(summaries)
    
    def _print_recommendations(self, summaries: List[ModelBenchmarkSummary]) -> None:
        """Print recommendations based on benchmark results."""
        best_performance = summaries[0]
        most_efficient = min(summaries, key=lambda x: x.model_memory_mb)
        fastest_loading = min(summaries, key=lambda x: x.load_time)
        
        self.console.print(Panel(
            f"🥇 Fastest: {best_performance.model_name} "
            f"({best_performance.avg_tokens_per_second:.1f} tokens/sec)\n"
            f"💾 Most Memory Efficient: {most_efficient.model_name} "
            f"({most_efficient.model_memory_mb:.0f}MB)\n"
            f"⚡ Fastest Loading: {fastest_loading.model_name} "
            f"({fastest_loading.load_time:.1f}s)",
            title="💡 Recommendations",
            border_style="cyan"
        ))
    
    def _get_performance_rating(self, tokens_per_sec: float) -> str:
        """Get performance rating text."""
        if tokens_per_sec > 100:
            return "🚀 Excellent Performance"
        elif tokens_per_sec > 50:
            return "⚡ Good Performance"
        elif tokens_per_sec > 20:
            return "✅ Acceptable Performance"
        else:
            return "⚠️  Slow Performance"
    
    def _get_performance_emoji(self, tokens_per_sec: float) -> str:
        """Get performance emoji."""
        if tokens_per_sec > 100:
            return "🚀"
        elif tokens_per_sec > 50:
            return "⚡"
        elif tokens_per_sec > 20:
            return "✅"
        else:
            return "⚠️"
    
    def _get_performance_color(self, tokens_per_sec: float) -> str:
        """Get color for performance level."""
        if tokens_per_sec > 100:
            return "green"
        elif tokens_per_sec > 50:
            return "yellow"
        elif tokens_per_sec > 20:
            return "orange"
        else:
            return "red"
    
    def _calculate_efficiency(self, summary: ModelBenchmarkSummary) -> float:
        """Calculate memory efficiency metric."""
        if summary.avg_tokens_per_second <= 0:
            return 0.0
        return summary.model_memory_mb / summary.avg_tokens_per_second
    
    def export_to_json(self, summaries: List[ModelBenchmarkSummary], filename: str) -> bool:
        """Export benchmark results to JSON."""
        try:
            import json
            from pathlib import Path
            
            # Convert summaries to dictionaries
            data = []
            for summary in summaries:
                data.append({
                    "model_id": summary.model_id,
                    "model_name": summary.model_name,
                    "load_time": summary.load_time,
                    "model_memory_mb": summary.model_memory_mb,
                    "total_memory_mb": summary.total_memory_mb,
                    "peak_memory_mb": summary.peak_memory_mb,
                    "successful_runs": summary.successful_runs,
                    "total_runs": summary.total_runs,
                    "avg_generation_time": summary.avg_generation_time,
                    "avg_tokens_per_second": summary.avg_tokens_per_second,
                    "max_tokens_per_second": summary.max_tokens_per_second,
                    "min_tokens_per_second": summary.min_tokens_per_second,
                    "system_info": summary.system_info,
                    "results": [
                        {
                            "run_id": r.run_id,
                            "prompt": r.prompt,
                            "generation_time": r.generation_time,
                            "tokens_generated": r.tokens_generated,
                            "tokens_per_second": r.tokens_per_second,
                            "memory_used_mb": r.memory_used_mb,
                            "success": r.success,
                            "error": r.error
                        }
                        for r in summary.results
                    ]
                })
            
            # Write to file
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported benchmark results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False


# Global reporter instance
benchmark_reporter = BenchmarkReporter()


def print_benchmark_report(summary: ModelBenchmarkSummary) -> None:
    """Print single model benchmark report."""
    benchmark_reporter.print_single_model_report(summary)


def print_comparison_report(summaries: List[ModelBenchmarkSummary]) -> None:
    """Print model comparison report."""
    benchmark_reporter.print_comparison_report(summaries)


def export_results_to_json(summaries: List[ModelBenchmarkSummary], filename: str) -> bool:
    """Export benchmark results to JSON file."""
    return benchmark_reporter.export_to_json(summaries, filename)