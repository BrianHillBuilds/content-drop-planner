# Content Drop Planner

A small Python utility that converts a simple Markdown or CSV content calendar into a sorted, dated posting schedule.

It is useful when content ideas are planned in a lightweight document but the publishing order needs to be checked, shared, or imported into another workflow.

## Features

- Reads CSV calendars and Markdown tables or pipe-delimited list items
- Sorts content by date, channel, and topic
- Expands simple recurring CSV items with `repeat_days` and `occurrences`
- Writes a Markdown schedule, a CSV schedule, or both
- Uses only Python's standard library

## Requirements

- Python 3.10 or newer

## CSV input

Use these columns:

```csv
date,channel,topic,format,notes,repeat_days,occurrences
2026-11-03,Instagram,Product launch teaser,Reel,Review final caption,,
2026-11-05,Newsletter,Weekly roundup,Email,Include the newest guide,7,3
```

Required columns are `date`, `channel`, and `topic`. Dates must use `YYYY-MM-DD` format. `format`, `notes`, `repeat_days`, and `occurrences` are optional.

## Markdown input

A Markdown table works:

```markdown
| Date | Channel | Topic | Format | Notes |
| --- | --- | --- | --- | --- |
| 2026-11-03 | Instagram | Product launch teaser | Reel | Review final caption |
```

So does a simple list:

```markdown
- 2026-11-04 | Blog | Getting started guide | Article | Add screenshots
```

## Run it

Print a Markdown schedule:

```bash
python3 planner.py examples/calendar.csv
```

Write both Markdown and CSV schedules:

```bash
python3 planner.py examples/calendar.csv \
  --markdown-output examples/posting_schedule.md \
  --csv-output examples/posting_schedule.csv
```

## Example files

- `examples/calendar.csv` — sample input calendar, including one recurring item
- `examples/calendar.md` — the same planning style in Markdown form
- `examples/posting_schedule.md` — generated Markdown output
- `examples/posting_schedule.csv` — generated CSV output

## License

MIT — see [LICENSE](LICENSE).
