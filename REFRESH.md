# Data Refresh Guide (Internal — Socio Use Only)

## When to refresh

The American Community Survey (ACS) 5-Year estimates are released annually in December.
When a new vintage is available, refresh the tool with updated data.

## How to refresh

### Step 1: Update the vintage year

In `config.py`, update:
```python
ACS_VINTAGE = 2024  # Change to the new vintage year
```

### Step 2: Clear cached data

```bash
rm -rf data/cache/acs_housing.csv
rm -rf data/cache/block_groups_enriched.csv
# Do NOT delete gazetteer or county boundaries — these are 2020 geography (static until 2030)
# Do NOT delete opportunity_atlas.csv unless they've released new data
```

### Step 3: Rebuild

```bash
cd building_trends_explorer
python build_map.py
```

This will:
1. Fetch fresh ACS data from the Census API (takes ~30 seconds)
2. Re-merge with existing Gazetteer centroids and Opportunity Atlas data
3. Re-classify growth tiers
4. Generate a new HTML file

### Step 4: QA

Open `output/utah_building_trends.html` in a browser and verify:
- Map loads correctly
- Markers display across Utah
- Growth tier distribution looks reasonable
- Popups show the updated ACS vintage in the source label
- File size is reasonable (< 10 MB)

Run the test suite:
```bash
pytest tests/ -v
```

### Step 5: Deliver

Send the updated `utah_building_trends.html` to Envision Utah's web team
for a file swap on their server.

## Data sources referenced

| Source | URL | Update frequency |
|--------|-----|-----------------|
| ACS 5-Year Estimates | https://data.census.gov | Annual (December) |
| Census Gazetteer (2020) | https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html | Decennial (next: 2030) |
| Opportunity Atlas | https://opportunityinsights.org/data/ | Irregular (based on research releases) |
| TIGER/Line Tract Boundaries | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html | Decennial (next: 2030) |

## Troubleshooting

**Census API returns 404:** The vintage year may not exist yet. Check
https://api.census.gov/data.html for available vintages.

**Census API returns 204 / empty:** Some variables may have been renamed or
discontinued in the new vintage. Check the ACS variable list for the new year:
https://api.census.gov/data/{vintage}/acs/acs5/variables.html

**Row count changes significantly:** Block group boundaries are updated with
each decennial census. If the 2030 Census creates new boundaries, the Gazetteer
file and tract shapefiles will need to be re-downloaded. GEOIDs will change.

**Growth tier distribution looks wrong:** The tier thresholds in config.py are
based on the 2023 data distribution. A new vintage with very different construction
patterns might need threshold adjustments. Check the summary stats in the build log.
