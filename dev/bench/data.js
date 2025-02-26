window.BENCHMARK_DATA = {
  "lastUpdate": 1740600683706,
  "repoUrl": "https://github.com/flip555/home_energy_hub",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "109870462+flip555@users.noreply.github.com",
            "name": "flip555",
            "username": "flip555"
          },
          "committer": {
            "email": "109870462+flip555@users.noreply.github.com",
            "name": "flip555",
            "username": "flip555"
          },
          "distinct": true,
          "id": "9ebeabb9936eefb60c99b600ac2dd698599fc800",
          "message": "Update test-and-scan.yml",
          "timestamp": "2025-02-26T20:10:23Z",
          "tree_id": "c2de8461b2f6f4e23cc85258eacd1bc5c5677666",
          "url": "https://github.com/flip555/home_energy_hub/commit/9ebeabb9936eefb60c99b600ac2dd698599fc800"
        },
        "date": 1740600683506,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/performance/test_benchmark.py::test_core_operations",
            "value": 24990.978411560332,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024741600946328004",
            "extra": "mean: 40.01443975228356 usec\nrounds: 23420"
          },
          {
            "name": "tests/performance/test_benchmark.py::test_data_processing",
            "value": 1735.510617529727,
            "unit": "iter/sec",
            "range": "stddev: 0.000009909306128309217",
            "extra": "mean: 576.1992982926084 usec\nrounds: 1113"
          },
          {
            "name": "tests/performance/test_benchmark.py::test_memory_operations",
            "value": 543.4580331118256,
            "unit": "iter/sec",
            "range": "stddev: 0.00003219611885972016",
            "extra": "mean: 1.8400684856455756 msec\nrounds: 418"
          }
        ]
      }
    ]
  }
}