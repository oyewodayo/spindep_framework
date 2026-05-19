# SPINDEP — CPT Analysis Platform

Production-grade TypeScript/React frontend for spin-dependent CPT asymmetry analysis.
Designed for adoption by HEP research labs (CERN, Fermilab, DESY, etc.).

---

## Project Structure

```
src/
├── App.tsx                          # Root component — wires layout + routing
│
├── types/
│   └── index.ts                     # All domain + UI TypeScript interfaces
│
├── constants/
│   ├── index.ts                     # Design tokens, nav config, pipeline steps, thresholds
│   └── styles.ts                    # Global CSS string (injected once at mount)
│
├── api/
│   └── client.ts                    # Typed API client — all fetch calls in one place
│
├── hooks/
│   └── index.ts                     # Custom hooks:
│                                    #   useApiHealth      — polls /api/status every 5 s
│                                    #   usePipelineJob    — polls running job, emits progress
│                                    #   usePipeline       — orchestrates run → poll → results
│                                    #   useSort           — generic sortable-column helper
│                                    #   useCopyToClipboard
│
├── utils/
│   └── index.ts                     # Pure functions: pval coloring, LaTeX generation,
│                                    #   log colorization, fallback tree, safeId, etc.
│
└── components/
    ├── ui/
    │   ├── Icon.tsx                 # Single icon component backed by an SVG registry
    │   ├── FileTree.tsx             # Recursive dataset directory browser
    │   └── index.tsx                # Stat, PanelHeader, ChartTooltip, SigTag,
    │                                #   ApiBanner, ProgressBar, SearchBar
    │
    ├── layout/
    │   ├── Sidebar.tsx              # Navigation sidebar + API status + results summary
    │   └── Topbar.tsx               # Page title + live result badges
    │
    └── sections/
        ├── IngestSection.tsx        # Dataset preview + pipeline launch buttons
        ├── PipelineSection.tsx      # Step tracker + live log stream
        ├── BatchResultsSection.tsx  # Sortable/filterable results table
        ├── PairDetail.tsx           # Per-pair coupling bound + Aα charts
        ├── GapAnalysisSection.tsx   # Coverage heat map
        ├── AtlasSection.tsx         # Constraint curve browser (coupling × potential)
        └── ExportSection.tsx        # Download panel + LaTeX copy
```

---

## Architectural Decisions

| Concern | Approach |
|---|---|
| **API** | Single typed `apiClient` object in `api/client.ts`. All fetch logic lives here — no inline `fetch` calls in components. |
| **State** | Business state (`pairs`, `jobId`, `resultsReady`) lives in `App.tsx` via `usePipeline`. UI state (sort, filter, selection) is local to each section. |
| **Side effects** | Encapsulated in custom hooks (`useApiHealth`, `usePipelineJob`). Components are pure renderers. |
| **Types** | Centralised in `types/index.ts`. Domain models (`AnalysisPair`, `DataPoint`) are separate from UI state types (`SortConfig`, `FilterState`). |
| **Constants** | Design tokens and configuration in `constants/index.ts`. No magic numbers in components. |
| **Utilities** | Pure, testable functions in `utils/index.ts`. No side effects. |
| **Styling** | CSS-in-JS string (injected once) keeps zero build-tooling dependency. Swap to CSS Modules or Tailwind without touching component logic. |

---

## Adding a new section

1. Add your route id to `NavSection` in `types/index.ts`
2. Add a nav item to `NAV_ITEMS` in `constants/index.ts`
3. Create `src/components/sections/MySection.tsx`
4. Add a `case` to the `renderPage()` switch in `App.tsx`

---

## API Contract (FastAPI backend)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/run?mode={mode}` | Submit pipeline job → `{ job_id }` |
| `GET`  | `/api/job/{job_id}` | Poll job → `{ status, log[] }` |
| `GET`  | `/api/results/{job_id}` | Fetch results → `{ pairs[], meta }` |
| `GET`  | `/api/status` | Health check → `{ version, uptime, … }` |
| `GET`  | `/api/tree` | Dataset directory tree → `FileTreeNode` |

---

## Extending for lab deployment

- **Auth**: Add an `Authorization` header to `apiClient.request()` — single touch point.
- **Multi-experiment**: Add an experiment selector to `Topbar`; pass it through `usePipeline` into `apiClient.run()`.
- **WebSocket log streaming**: Replace the polling loop in `usePipelineJob` with a `WebSocket` connection — no component changes needed.
- **Theming**: All colours are in `constants/index.ts` (`T`). Swap the palette for a CERN/Fermilab brand variant without touching any component file.