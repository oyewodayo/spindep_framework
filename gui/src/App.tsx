import React, { useEffect, useState, useCallback } from "react";
import { GLOBAL_CSS } from "./constants/styles";
import { useApiHealth, usePipeline } from "./hooks";
import { SIG } from "./constants";

import { Sidebar }  from "./components/layout/Sidebar";
import { Topbar }   from "./components/layout/Topbar";

import { IngestSection }       from "./components/sections/IngestSection";
import { PipelineSection }     from "./components/sections/PipelineSection";
import { BatchResultsSection } from "./components/sections/BatchResultsSection";
import { AtlasSection }        from "./components/sections/AtlasSection";
import { GapAnalysisSection }  from "./components/sections/GapAnalysisSection";
import { ExportSection }       from "./components/sections/ExportSection";

import type { NavSection, PipelineMode } from "./types";

// ─── CSS Injection ─────────────────────────────────────────────────────────────

function useGlobalStyles() {
    useEffect(() => {
        const el = document.createElement("style");

        el.textContent = GLOBAL_CSS;

        document.head.appendChild(el);

        return () => {
            document.head.removeChild(el);
        };
    }, []);
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  useGlobalStyles();

  const [page, setPage] = useState<NavSection>("ingest");
  const apiOnline       = useApiHealth();
  const { jobId, mode, pairs, resultsReady, startRun, handleComplete } = usePipeline();

  const significantPairs = pairs.filter(p => p.pval < SIG.STANDARD).length;

  const handleStartRun = useCallback(
    async (m: PipelineMode) => {
      setPage("pipeline");
      await startRun(m);
    },
    [startRun]
  );

  const handlePipelineComplete = useCallback(async () => {
    await handleComplete();
    setTimeout(() => setPage("batch"), 800);
  }, [handleComplete]);

  // ── Page renderer ────────────────────────────────────────────────────────────
  const renderPage = () => {
    switch (page) {
      case "ingest":
        return (
          <IngestSection onStartRun={handleStartRun} apiOnline={apiOnline} />
        );
      case "pipeline":
        return (
          <PipelineSection
            mode={mode}
            jobId={jobId}
            onComplete={handlePipelineComplete}
          />
        );
      case "batch":
      case "pairs":
        return <BatchResultsSection pairs={pairs} />;
      case "atlas":
        return <AtlasSection pairs={pairs} />;
      case "gaps":
        return <GapAnalysisSection pairs={pairs} />;
      case "export":
        return <ExportSection pairs={pairs} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        activePage={page}
        onNavigate={setPage}
        apiOnline={apiOnline}
        resultsReady={resultsReady}
        totalPairs={pairs.length}
        significantPairs={significantPairs}
      />

      <div className="main-area">
        <Topbar
          activePage={page}
          apiOnline={apiOnline}
          resultsReady={resultsReady}
          totalPairs={pairs.length}
          significantPairs={significantPairs}
        />
        <div className="workspace">{renderPage()}</div>
      </div>
    </div>
  );
}