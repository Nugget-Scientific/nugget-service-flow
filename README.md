# Nugget Service Scheduling Flow

An interactive, horizontally-scrollable view of the service ticket lifecycle —
from how work first becomes a ticket, through scheduling, to close. Built for
onboarding and reference by the Field Service team.

**Live site:** https://nugget-scientific.github.io/nugget-service-flow/

## What it shows

The flowchart maps a service ticket from intake to close:

- **How work arrives** (violet) — the four intake channels: routine service
  coming due, a client emailing support, a new sale, and in-person / text
  "shoulder taps." All land in Triage.
- **Lifecycle** (blue) — the happy path: Triage → Scheduling Required →
  Tentatively/Pending → Booked → Working → Resolved → Report Sent → Closed.
- **Exception / off-ramp** (tan) — Awaiting Info, Awaiting Parts, Escalated to
  SME, Monitoring, and Client Canceled, with the edges back into the queue.
- **Closed** (green) — the terminal state, with dashed follow-up loops that open
  a fresh ticket back at Triage.

Each process node is **dual-encoded**: the *fill* is its phase (above) and the
*border color* is the owning role — Dispatcher/Scheduler, Field Engineer, Sales,
SME, Procurement/Parts, Account Mgr/Service Lead, or Client. The owner key runs
across the bottom of the page and the exported PNG. (The ownership mapping is a
strawman pending sign-off; recolor via the `style ...` lines at the bottom of
the `.mmd`.)

## Viewing

Open `index.html` in a browser, or visit the live site. Drag to pan, use the
`+` / `−` buttons (or `Cmd`/`Ctrl` + scroll) to zoom, and `Fit` to reset. The
`PNG` button downloads the full-resolution image.

## Editing the diagram

The source of truth is [`src/service_lifecycle.mmd`](src/service_lifecycle.mmd),
a [Mermaid](https://mermaid.js.org/) flowchart. Edit it, then rebuild the
published assets:

```bash
bash src/build.sh
```

That regenerates `assets/diagram.svg` (vector, used by the site) and
`assets/diagram.png` (the branded, header-stamped download). Commit the updated
`src/` and `assets/`, push to `main`, and Pages redeploys automatically.

### Notes for editors

- The top-level `fontFamily` in the `.mmd` front-matter must stay set — it fixes
  the sans-serif font *before* layout so Mermaid measures and renders in the same
  font. Setting it only via CSS clips labels, because the `-C` stylesheet is
  applied after layout.
- Node colors are defined by the `classDef`s at the bottom of the `.mmd`; keep
  them in sync with the legend in `index.html` and the palette in
  `src/compose.py`.

## Layout

```
index.html              the viewer (self-contained: HTML + CSS + JS, no deps)
.nojekyll               tells GitHub Pages to serve files as-is
assets/diagram.svg      vector diagram embedded by the viewer
assets/diagram.png      branded, header-stamped raster for download / preview
assets/logo.png         Nugget Scientific logo
src/service_lifecycle.mmd   Mermaid source (edit this)
src/style.css           cosmetic Mermaid overrides (rounded corners, label size)
src/compose.py          paints the title + logo header onto the PNG
src/build.sh            renders the source and runs the compose step
```
