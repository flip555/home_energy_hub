import pytest
from datetime import datetime
from pathlib import Path
import json

# Basic performance test
def test_basic_performance():
    """Basic performance test to ensure benchmarking works."""
    result = 1 + 1
    assert result == 2

@pytest.mark.benchmark(group="core")
def test_core_operations(benchmark):
    """Benchmark core operations."""
    def core_op():
        # Simulate core operations
        for i in range(1000):
            _ = i * 2
    
    benchmark(core_op)

@pytest.mark.benchmark(group="data_processing")
def test_data_processing(benchmark):
    """Benchmark data processing operations."""
    def process_data():
        # Simulate data processing
        data = list(range(10000))
        processed = [x * 2 for x in data]
        return len(processed)
    
    result = benchmark(process_data)
    assert result == 10000

@pytest.mark.benchmark(group="memory")
def test_memory_operations(benchmark):
    """Benchmark memory-intensive operations."""
    def memory_op():
        # Simulate memory operations
        large_list = [i for i in range(50000)]
        return sum(large_list)
    
    result = benchmark(memory_op)
    assert result == 1249975000
@pytest.fixture
def benchmark_storage(request, benchmark):
    """Custom fixture to store benchmark results."""
    yield benchmark
    
    # Store results after test completion
    results_dir = Path(__file__).parent / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # Create a timestamp-based filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = results_dir / f'benchmark_{timestamp}.json'
    
    # Store the benchmark results
    with open(result_file, 'w') as f:
        json.dump(benchmark.stats, f, indent=2)
