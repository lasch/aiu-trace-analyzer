# Testing

## HowToRun

To run all tests, just run:
```
pytest
```

To run a specific file and also see the output of the test:
```
pytest -s <file_name>
```


## Basics/Best practices:

 * Unit tests to cover all functions that are implemented
 * Consider tests are expected to fail (not just the good cases)
 * Add new tests for issues that got fixed
 * keep things a tidy as possible (minimize the amount of extra test data)
 * One test function should only assert one condition (recommended for easier debugging but not always useful)

## Examples of test mechanisms:

 * [basic parameterized tests including fail-cases](aiu_trace_analyzer/pipeline/test_mappings.py)
 * [running top-level python via pytest](acelyzer/test_acelyzer.py)
 * [Creating class instance and check variables](aiu_trace_analyzer/pipeline/test_rcu_utilization.py)
 * [Generate input data for test cases](aiu_trace_analyzer/inout/test_ingestion.py) based on [generator fixtures](conftest.py)


 ## Misc:

  * If you need to add/change the paths to search for tests or python files, check the settings in [pytest.ini](../pytest.ini)
