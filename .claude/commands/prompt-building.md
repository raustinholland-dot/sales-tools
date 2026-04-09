# /prompt-building — Input-Output Batch Mapper

## Overview

This command sets up an interactive HTML-based batch mapper tool for mapping inputs (emails, Teams messages, calendar events) to their corresponding outputs (files to update, tasks to create, etc.).

The tool helps build ground-truth training data for creating intelligent prompts that automate response generation.

## What It Does

1. **Displays inputs chronologically** — All inputs sorted by time (earliest first)
2. **Shows full input details** — When you click an input, see all metadata
3. **Maps inputs to outputs** — For each input, view/edit what files should be updated
4. **Batch selection** — Group multiple inputs together and map them as a unit
5. **Refresh function** — Reset to the earliest input anytime

## Files Involved

```
~/Desktop/sales-tools/
├── batch-mapper.html           (Main HTML app)
├── input-output-chronological.html  (Alternative chronological view)
├── input-output-map.md         (Ground truth data file)
└── scoreboard.html             (Stats dashboard)
```

## How to Run

### Start the HTTP Server

```bash
cd ~/Desktop/sales-tools/
python3 -m http.server 8889 > /tmp/local-server.log 2>&1 &
```

### Open in Browser

```
http://localhost:8889/batch-mapper.html
```

## Architecture

### Data Structure

The batch mapper uses:

1. **Inputs Array** — Each input has:
   - `id` — unique identifier (INPUT-001, etc.)
   - `time` — timestamp (format: "2026-04-01 08:32 AM CT")
   - `from` — sender
   - `type` — "email", "teams", or "calendar"
   - `subject` — subject line
   - `preview` — body content preview

2. **Input-Output Map** — Dictionary mapping input IDs to outputs:
   ```javascript
   inputOutputMap["INPUT-001"] = [
       { desc: "Update memory", file: "memory/2026-04-01.md", condition: "always" },
       { desc: "Create event", file: "ops/events/index.md", condition: "always" }
   ]
   ```

### Key Functions

- **resetToEarliest()** — Load earliest input, clear selection
- **toggleInputSelection(inputId)** — Select/deselect input and show details
- **showFullInputDetails(inputId)** — Display all input metadata
- **showInputOutputs(inputId)** — Show outputs for that input
- **createNewBatch()** — Group selected inputs as a batch
- **saveBatch()** — Save batch mapping to local storage
- **exportAllMappings()** — Export all batches as markdown

## Workflow

1. **Page loads** → Shows earliest input + outputs
2. **Click an input** → See full details + corresponding outputs
3. **Select multiple inputs** → Create a batch
4. **Edit outputs** → Add/remove/modify output mappings
5. **Save batch** → Store the input-output mapping
6. **Refresh** → Reset to earliest, start over

## Technical Notes

- Uses vanilla JavaScript (no frameworks)
- Runs client-side only (no server backend)
- Time parsing: "2026-04-01 08:32 AM CT" format
- Sorting by time: converts to ISO for comparison
- Responsive grid layout (HTML5/CSS3)

---

**Created:** 2026-04-02
**Status:** Active development
