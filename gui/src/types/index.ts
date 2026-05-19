// ─── Domain Types ─────────────────────────────────────────────────────────────

export type CouplingType = "gAgA" | "gsgs" | "gVgV" | "gpgp" | "gpgs" | string;
export type PotentialType = "Yukawa" | "power-law" | string;
export type PipelineMode = "full" | "validate" | "gaps" | "atlas";
export type JobStatus = "queued" | "running" | "done" | "error";
export type NavSection = "ingest" | "pipeline" | "batch" | "pairs" | "atlas" | "gaps" | "export";

export interface DataPoint {
  logLam: number;
  logGm: number;
  logGa: number;
  A: number;
}

export interface AnalysisPair {
  // Identity
  id: string;
  coupling: CouplingType;
  potential: PotentialType;

  // Sectors
  secM: string;           // matter sector label (e.g. "ee", "ep")
  secA: string;           // antimatter sector label
  interactionClass: string; // e.g. "lepton-lepton", "lepton-nucleon"

  // Dataset metadata
  matterDataset: string;     // e.g. "Delaunay2017"
  antimatterDataset: string; // e.g. "Adkins2022"
  matterUnit: string;        // e.g. "m", "m (pre-converted)"
  antimatterUnit: string;

  // Core statistics
  meanAbsA: number;         // mean |Aα|
  chi2Weighted: number;     // χ² with per-point curvature weights
  chi2Uniform: number;      // χ² with uniform 10% uncertainty
  chi2Ratio: number;        // chi2Weighted / chi2Uniform — <1 means weighted is more conservative
  pval: number;             // p-value (weighted) — preferred for thesis
  pvalUniform: number;      // p-value (uniform)
  dof: number;

  // Uncertainty estimates
  sigmaM: number;           // mean σ_matter (%)
  sigmaA: number;           // mean σ_antimatter (%)

  // Lambda range
  lambdaMin: number;
  lambdaMax: number;

  // Per-point data for charts
  points: DataPoint[];
}

export interface PipelineJob {
  job_id: string;
  status: JobStatus;
  log: string[];
  created_at: string;
  completed_at?: string;
}

export interface PipelineResults {
  pairs: AnalysisPair[];
  meta: {
    run_id: string;
    mode: PipelineMode;
    completed_at: string;
    n_pairs: number;
    n_significant: number;
  };
}

export interface FileTreeNode {
  name: string;
  type: "folder" | "file";
  rows?: number;
  children?: FileTreeNode[];
}

export interface ApiStatus {
  version: string;
  uptime: number;
  datasets_path: string;
}

// ─── UI State Types ────────────────────────────────────────────────────────────

export interface SortConfig<T> {
  key: keyof T;
  direction: "asc" | "desc";
}

export interface FilterState {
  query: string;
  coupling: CouplingType | "All";
}

export interface CoverageCell {
  coupling: CouplingType;
  potential: PotentialType;
  paired: number;
}

export interface TooltipPayloadItem {
  name: string;
  value: number;
  color?: string;
}