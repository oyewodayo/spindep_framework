import React from "react";
import { T, SIG } from "../../constants";
import { buildLatexTable } from "../../utils";
import { PanelHeader } from "../ui";
import { Icon } from "../ui/Icon";
import { useCopyToClipboard } from "../../hooks";
import type { AnalysisPair } from "../../types";

interface ExportSectionProps {
  pairs: AnalysisPair[];
}

interface OutputSpec {
  label: string;
  icon: string;
  desc: string;
  size: string;
  ext: string;
}

const OUTPUTS: OutputSpec[] = [
  { label: "PDF Report",           icon: "report",   desc: "Full analysis report with all plots and tables",        size: "~4 MB",  ext: "pdf"  },
  { label: "Summary CSV",          icon: "table",    desc: "All pair results: χ², p-values, |Aα|, lambda ranges",  size: "~18 KB", ext: "csv"  },
  { label: "Asymmetry plots",      icon: "chart",    desc: "Per-pair coupling and asymmetry figures (PNG 300 DPI)", size: "~12 MB", ext: "zip"  },
  { label: "Constraint atlas",     icon: "layers",   desc: "All atlas figures, one per coupling × potential",       size: "~8 MB",  ext: "zip"  },
  { label: "Gap analysis figures", icon: "scope",    desc: "Coverage matrix, λ-space gap plot",                    size: "~1 MB",  ext: "zip"  },
  { label: "LaTeX tables",         icon: "copy",     desc: "Publication-ready .tex tables for significant results", size: "~6 KB",  ext: "tex"  },
  { label: "HDF5 data archive",    icon: "dl",       desc: "All interpolated g(λ) and A_α(λ) arrays",              size: "~22 MB", ext: "h5"   },
  { label: "YAML config used",     icon: "settings", desc: "Reproducibility: exact config that produced this run", size: "<1 KB",  ext: "yaml" },
];

export const ExportSection: React.FC<ExportSectionProps> = ({ pairs }) => {
  const sig             = pairs.filter(p => p.pval < SIG.STANDARD);
  const { copiedKey, copy } = useCopyToClipboard();
  const latexTable      = buildLatexTable(pairs);

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
          Export &amp; Report
        </h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>
          Results are written to{" "}
          <span style={{ fontFamily: T.mono, color: T.blue }}>
            ~/spindep_framework/results/
          </span>{" "}
          on the server after each run.
        </p>
      </div>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 20 }}
      >
        {OUTPUTS.map(o => (
          <div
            key={o.label}
            className="panel"
            style={{ display: "flex", alignItems: "center", padding: 0 }}
          >
            <div
              style={{
                padding: "14px 14px 14px 16px",
                display: "flex",
                alignItems: "center",
                gap: 12,
                flex: 1,
              }}
            >
              <span style={{ color: T.blue, flexShrink: 0 }}>
                <Icon name={o.icon as any} size={18} />
              </span>
              <div>
                <div
                  style={{ fontWeight: 600, color: T.textHi, fontSize: 13, marginBottom: 2 }}
                >
                  {o.label}
                </div>
                <div style={{ fontSize: 11, color: T.textDim }}>{o.desc}</div>
              </div>
            </div>
            <div
              style={{
                padding: "0 14px",
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-end",
                gap: 6,
                flexShrink: 0,
              }}
            >
              <span className="tag tag-muted" style={{ fontFamily: T.mono }}>
                {o.size}
              </span>
              <button className="btn btn-ghost" style={{ fontSize: 11, padding: "4px 10px" }}>
                <Icon name="dl" size={11} /> .{o.ext}
              </button>
            </div>
          </div>
        ))}
      </div>

      {sig.length > 0 && (
        <div className="panel">
          <PanelHeader
            title="LaTeX Table (significant results)"
            icon="copy"
            right={
              <button
                className="btn btn-ghost"
                style={{ fontSize: 11 }}
                onClick={() => copy("latex", latexTable)}
              >
                {copiedKey === "latex" ? (
                  <><Icon name="check" size={12} /> Copied</>
                ) : (
                  <><Icon name="copy" size={12} /> Copy</>
                )}
              </button>
            }
          />
          <pre
            className="code-block"
            style={{
              margin: 0,
              borderRadius: "0 0 10px 10px",
              maxHeight: 220,
              overflowY: "auto",
              fontSize: 11,
            }}
          >
            {latexTable}
          </pre>
        </div>
      )}
    </div>
  );
};