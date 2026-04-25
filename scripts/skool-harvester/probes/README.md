# Probes

One-off scripts that confirmed Skool's page structure when the harvester
was being built. Run these only when Skool ships a layout change and the
walker stops finding lessons.

| Script | What it confirms |
|---|---|
| `probe_classroom.py` | Classroom root page selectors + `__NEXT_DATA__` shape |
| `probe_course.py`    | Course detail page module tree under `course.children` |
| `probe_pagination.py`| Pagination query param (`?p=N`) and page-size behavior |

Each writes its findings under `workspace/skool-harvest/<community>/_*.{html,json}`
for inspection.

If you re-probe and find the SSR shape has changed, update the parsing in
`scripts/skool-harvester/skool_walk.py` to match the new keys.
