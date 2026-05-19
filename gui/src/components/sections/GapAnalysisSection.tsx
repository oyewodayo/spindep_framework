import React, { useMemo, useState } from "react";
import { T } from "../../constants";
import { PanelHeader } from "../ui";
import { Icon } from "../ui/Icon";
import type { AnalysisPair, CoverageCell } from "../../types";

interface GapAnalysisSectionProps {
  pairs: AnalysisPair[];
}

function cellBackground(val: number, max: number): string {
  if (val === 0) return T.bg0;
  return `rgba(74,158,255,${0.15 + (val / max) * 0.7})`;
}

export const GapAnalysisSection: React.FC<GapAnalysisSectionProps> = ({ pairs }) => {
  const [hover, setHover] = useState<(CoverageCell & { coupling: string }) | null>(null);

  const couplings  = useMemo(() => [...new Set(pairs.map(p => p.coupling))].sort(), [pairs]);
  const potentials = useMemo(() => [...new Set(pairs.map(p => p.potential))].sort(), [pairs]);

  const matrix = useMemo(
    () =>
      couplings.map(coupling => ({
        coupling,
        coverage: potentials.map(potential => ({
          potential,
          paired: pairs.filter(p => p.coupling === coupling && p.potential === potential).length,
        })),
      })),
    [pairs, couplings, potentials]
  );

  const maxPairs = Math.max(1, ...matrix.flatMap(r => r.coverage.map(c => c.paired)));

  if (pairs.length === 0) {
    return (
      <div className="fade-in" style={{ textAlign: "center", padding: 60, color: T.muted }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: T.textDim }}>
          Run the pipeline first to see gap analysis
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
          Gap Analysis
        </h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>
          Coverage matrix built from real pipeline results.
        </p>
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <PanelHeader
          title="Coverage Matrix: Matched Pairs per (Coupling × Potential)"
          icon="grid"
          sub="Number of matched matter–antimatter pairs. Dark = no experimental data."
        />
        <div style={{ padding: 20, overflowX: "auto" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `120px repeat(${potentials.length}, 1fr)`,
              gap: 4,
              minWidth: 400,
            }}
          >
            {/* Header row */}
            <div />
            {potentials.map(p => (
              <div
                key={p}
                style={{
                  textAlign: "center",
                  fontSize: 10,
                  color: T.textDim,
                  fontFamily: T.mono,
                  fontWeight: 600,
                  padding: "4px 0",
                }}
              >
                {p}
              </div>
            ))}

            {/* Data rows */}
            {matrix.map(row => (
              <React.Fragment key={row.coupling}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    fontSize: 11,
                    fontFamily: T.mono,
                    color: T.blue,
                    fontWeight: 600,
                    paddingRight: 8,
                  }}
                >
                  {row.coupling}
                </div>
                {row.coverage.map((cell, j) => (
                  <div
                    key={j}
                    className="heat-cell"
                    style={{
                      height: 44,
                      background: cellBackground(cell.paired, maxPairs),
                      border: `1px solid ${T.border}`,
                      color: cell.paired > 0 ? T.textHi : T.muted,
                    }}
                    onMouseEnter={() =>
                      setHover({ ...cell, coupling: row.coupling })
                    }
                    onMouseLeave={() => setHover(null)}
                  >
                    {cell.paired > 0 ? cell.paired : <Icon name="close" size={10} />}
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>

          {hover && (
            <div
              style={{
                marginTop: 12,
                padding: "8px 14px",
                background: T.bg2,
                border: `1px solid ${T.border}`,
                borderRadius: 6,
                fontSize: 12,
                display: "inline-flex",
                gap: 20,
              }}
            >
              <span style={{ fontFamily: T.mono, color: T.blue }}>
                {hover.coupling} · {hover.potential}
              </span>
              <span>
                Pairs:{" "}
                <b style={{ color: hover.paired > 0 ? T.teal : T.red }}>{hover.paired}</b>
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};