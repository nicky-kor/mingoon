# Cross-Industry Technology Transfer Radar

This is the project's core differentiator (spec section 4): finding
technology proven in another industry and evaluating whether it could
transfer to Battery Manufacturing.

## Chain

```
Original Industry -> Technology -> Industrial Problem -> Evidence
    -> Potential Battery Application -> Feasibility -> Potential Benefit
    -> Research Question
```

## Why industry classification and transfer target are kept separate

A document about steel rolling-mill vibration diagnosis should be
classified `industry=steel`, *not* `industry=battery_manufacturing`, even
though "rolling mill" is also a keyword used to identify battery
*calendering* equipment (`config/battery.yaml`). Conflating the two would
hide the transfer opportunity instead of surfacing it. So:

- `processing/classify.classify_industry()` uses a small set of
  battery-*identity* terms only (battery, lithium-ion, cathode, anode,
  electrolyte, gigafactory, ...) to decide if a document *is about* battery
  manufacturing.
- `processing/classify.classify_battery_process()` and
  `agents/transfer.py` use the full `config/battery.yaml` process/equipment
  keyword lists to find which battery process a *non-battery* document's
  technology could plausibly transfer to.

This is exactly the steel → rolling mill → battery calendering example
from the spec.

## TransferAgent (`agents/transfer.py`)

Runs only for documents where `industry != battery_manufacturing` and a
`technology` was classified. Output fields match spec section 33:
`target_battery_process`, `target_equipment`, `expected_benefit`,
`implementation_difficulty`, `risk`, `transfer_confidence` (0-100),
`research_question`. Stored in the `transfer_opportunities` table.

- **With an LLM configured**: the prompt explicitly asks for a
  conservative assessment and forbids inventing citations/numbers.
- **Without one**: a heuristic scores confidence from keyword overlap
  between the document text and the battery process/equipment keyword
  lists, and marks its `expected_benefit`/`risk` fields as
  `INFERENCE`/`HYPOTHESIS` rather than stated fact (spec section 21).

## Where it surfaces

- `research-os report daily` / `weekly` — "Cross-Industry Transfer" /
  "Cross-Industry Transfer Radar" sections.
- `transfer_opportunities` table directly, for ad-hoc queries.
