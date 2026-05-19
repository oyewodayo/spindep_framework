import { T, SIG } from "../constants";

// ─── Statistics ───────────────────────────────────────────────────────────────

export function pvalColor(p: number): string {
  if (p < SIG.HIGHLY) return T.red;
  if (p < SIG.STANDARD) return T.amber;
  return T.green;
}

export function formatPval(p: number): string {
  if (p < 1e-9) return "<10⁻⁹";
  return p.toExponential(2);
}

export function formatLogScale(v: number): string {
  return `10^${v.toFixed(0)}`;
}

// ─── Log Line Coloring ─────────────────────────────────────────────────────────

export function logLineColor(line: string): string {
  if (line.includes("[OK]") || line.includes("OK"))   return T.teal;
  if (line.includes("[WARN]") || line.includes("WARN")) return T.amber;
  if (line.includes("[ERR]") || line.includes("ERROR") || line.includes("error")) return T.red;
  return T.textDim;
}

// ─── Data Helpers ──────────────────────────────────────────────────────────────

export function makeFallbackTree() {
  const COUPLINGS = ["gAgA", "gsgs", "gVgV", "gpgp", "gpgs"];
  return {
    name: "datasets/normalized",
    type: "folder" as const,
    children: COUPLINGS.map(c => ({
      name: c,
      type: "folder" as const,
      children: [{ name: "lepton-lepton", type: "folder" as const, children: [] }],
    })),
  };
}

export function estimateProgress(logLength: number): number {
  return Math.min(95, logLength * 4);
}

// ─── String Helpers ───────────────────────────────────────────────────────────

/** Sanitise a string for use as an SVG/HTML id. */
export function safeId(s: string): string {
  return s.replace(/[^a-z0-9]/gi, "_");
}

// ─── LaTeX Generation ─────────────────────────────────────────────────────────

import type { AnalysisPair } from "../types";

export function buildLatexTable(pairs: AnalysisPair[]): string {
  const sig = pairs.filter(p => p.pval < SIG.STANDARD);
  return `\\begin{table}[h]
\\centering
\\caption{CPT Asymmetry Test Results — Weighted \\(\\chi^2\\) Method}
\\label{tab:cpt_asymmetry}
\\begin{tabular}{llllccccr}
\\hline
Coupling & Potential & Class & Sectors & $\\langle|A_\\alpha|\\rangle$ & $\\chi^2_{\\mathrm{w}}$ & $\\chi^2_{\\mathrm{u}}$ & ratio & $p$-value \\\\
\\hline
${sig
  .slice(0, 12)
  .map(
    p =>
      `${p.coupling} & ${p.potential} & ${p.interactionClass ?? "—"} & $${p.secM} \\times \\bar{${p.secA}}$ & ${p.meanAbsA?.toFixed(4)} & ${p.chi2Weighted?.toFixed(0)} & ${p.chi2Uniform?.toFixed(0)} & ${p.chi2Ratio?.toFixed(3) ?? "—"} & ${p.pval?.toExponential(1)} \\\\`
  )
  .join("\n")}
\\hline
\\end{tabular}
\\begin{tablenotes}
  \\small
  \\item $\\chi^2_{\\mathrm{w}}$: per-point curvature-weighted. $\\chi^2_{\\mathrm{u}}$: uniform 10\\% uncertainty.
  \\item ratio $< 1$ indicates weighted method is more conservative (preferred).
  \\item $p$-values shown for weighted method. All entries: $p < 0.001$ (***).
\\end{tablenotes}
\\end{table}`;
}