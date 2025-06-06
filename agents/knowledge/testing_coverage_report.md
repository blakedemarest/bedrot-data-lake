# Initial Test Coverage

The first round of unit tests provides baseline coverage for core helper functions.

```
Name                                              Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------------
src/archive_old_data.py                              45     22    51%   26, 43-59, 62-66
src/distrokid/cleaners/distrokid_landing2raw.py      51     11    78%   55-56, 59-60, 63-69
src/metaads/cleaners/metaads_raw2staging.py          45      2    96%   25, 42
src/metaads/cleaners/metaads_staging2curated.py      32      9    72%   28-34, 49, 52-55
-------------------------------------------------------------------------------
TOTAL                                               173     44    75%
```

Uncovered modules include the Playwright extractors and additional cleaners.
Stub tests should be added for each remaining ETL script to drive coverage higher.
