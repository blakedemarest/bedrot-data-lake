
# Testing Coverage Strategy

This knowledge base entry outlines a collaborative approach to improving automated
testing across the data lake.  It draws on the "Testing Coverage" item in
`BEDROT_Data_Lake_Analysis.md` and provides a plan for multiple agents to work in
unison.

## Purpose

* Establish a unified testing framework.
* Coordinate three agents so they can safely build tests in parallel.
* Provide concrete steps for increasing coverage and integrating automation.

## High-Level Architectural Change

1. **Introduce a dedicated testing framework**
   - Create a `tests/` directory at the project root.
   - Adopt `pytest` and `pytest-cov` for unit and integration tests.

2. **Leverage the modular pipeline**
   - Mirror the ETL structure within `tests/` (e.g., `tests/distrokid`, `tests/tiktok`).
   - Write focused tests for extraction, validation, transformation, and loading.

3. **Automate test execution**
   - Add a CI workflow to run tests on every push and collect coverage reports.
   - Use coverage metrics to identify untested modules.

## Steps for More Granular Coverage

1. **Start with transformation logic**
   - Use small dataframe fixtures and assert expected outputs from cleaners.

2. **Add extraction and validation tests**
   - Mock network or browser interactions to test parsing without external calls.

3. **Test cross-zone workflows**
   - Run mini end-to-end pipelines on sample datasets to verify promotion and archiving logic.

4. **Focus on error handling**
   - Simulate failures (bad credentials, malformed files) and ensure graceful handling.

5. **Measure coverage and expand**
   - Generate reports with `pytest-cov` and iterate on uncovered code paths.

These steps align with the technical debt section of `BEDROT_Data_Lake_Analysis.md` and will provide a reliable testing foundation for future development.

## Multi-Agent Implementation Plan

To accelerate adoption, three specialized agents can collaborate:

1. **Framework Agent**
   - Scaffold the `tests/` directory and create subfolders for each data source
     (e.g., `tests/distrokid`, `tests/tiktok`).
   - Provide sample fixtures and a `pytest.ini` with sensible defaults.
   - Ensure `pytest` and `pytest-cov` appear in `requirements.txt`.

2. **Analysis Agent**
   - Survey the `src/` modules to determine critical paths highlighted in
     `BEDROT_Data_Lake_Analysis.md` (extractors, cleaners, loaders).
   - Produce an initial coverage report to identify gaps.
   - Suggest unit-test stubs for each uncovered module.

3. **CI Agent**
   - Configure a CI workflow (e.g., GitHub Actions) to run `pytest -q` with
     coverage on every push.
   - Upload coverage results as an artifact and fail the build on regressions.
   - Document how to run tests locally for parity with CI.

Agents should coordinate through pull requests and the knowledge base to avoid
overlap.  Once this foundation is established, incremental additions by any
agent will expand coverage over time.

## Example Directory Layout

```text
tests/
    conftest.py          # shared fixtures
    distrokid/
        test_extractors.py
        test_cleaners.py
    tiktok/
        test_extractors.py
        test_cleaners.py
    ...
```

This mirrors the `src/` hierarchy so each extractor or cleaner has a
corresponding test module.

## Next Steps

1. Framework Agent creates the folder structure and initial fixtures.
2. Analysis Agent identifies priority modules and writes the first unit tests.
3. CI Agent commits the workflow file and ensures it passes in the default
   branch.
