import React, { useState } from "react";
import { T } from "../../constants";
import { apiClient } from "../../api/client";
import { makeFallbackTree } from "../../utils";
import { ApiBanner, PanelHeader } from "../ui";
import { FileTree } from "../ui/FileTree";
import { Icon } from "../ui/Icon";
import type { FileTreeNode, PipelineMode } from "../../types";

interface IngestSectionProps {
  onStartRun: (mode: PipelineMode) => Promise<void>;
  apiOnline: boolean;
}

export const IngestSection: React.FC<IngestSectionProps> = ({
  onStartRun,
  apiOnline,
}) => {
  const [tree, setTree]               = useState<FileTreeNode | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileTreeNode | null>(null);

  const loadPreview = async () => {
    try {
      const data = await apiClient.getTree();
      setTree(data);
    } catch {
      setTree(makeFallbackTree());
    }
  };

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
          Dataset Ingest
        </h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>
          The pipeline reads from{" "}
          <span style={{ fontFamily: T.mono, color: T.blue, margin: "0 6px" }}>
            ~/spindep_framework/datasets/normalized/
          </span>
          on the server. Click <b style={{ color: T.textHi }}>Preview Structure</b> then run
          the pipeline.
        </p>
      </div>

      <ApiBanner online={apiOnline} />

      <div className="split split-2" style={{ marginBottom: 20, alignItems: "start" }}>
        {/* Drop zone */}
        <div>
          <div
            className={`drop-zone${tree ? " filled" : ""}`}
            onClick={loadPreview}
          >
            {tree ? (
              <>
                <div style={{ color: T.teal, marginBottom: 10 }}>
                  <Icon name="check" size={36} />
                </div>
                <div style={{ fontWeight: 600, color: T.textHi, marginBottom: 4 }}>
                  Dataset structure loaded
                </div>
                <div style={{ color: T.textDim, fontSize: 12 }}>
                  Reading from server: datasets/normalized/
                </div>
              </>
            ) : (
              <>
                <div style={{ color: T.muted, marginBottom: 12 }}>
                  <Icon name="folder" size={40} />
                </div>
                <div style={{ fontWeight: 600, color: T.textHi, marginBottom: 6 }}>
                  Click to preview dataset structure
                </div>
                <div style={{ color: T.textDim, fontSize: 12, marginBottom: 12 }}>
                  Data is read from the server filesystem — no upload needed
                </div>
                <div
                  style={{
                    fontFamily: T.mono,
                    fontSize: 11,
                    color: T.muted,
                    background: T.bg0,
                    borderRadius: 4,
                    padding: "6px 12px",
                    display: "inline-block",
                  }}
                >
                  datasets/normalized/<br />
                  ├── gAgA/lepton-lepton/*.csv<br />
                  ├── gsgs/lepton-nucleon/*.csv<br />
                  └── gVgV/nucleon-nucleon/*.csv
                </div>
              </>
            )}
          </div>
          {tree && (
            <div style={{ marginTop: 12 }}>
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => { setTree(null); setSelectedFile(null); }}
                title="Clear"
              >
                <Icon name="close" size={13} />
              </button>
            </div>
          )}
        </div>

        {/* File tree browser */}
        <div className="panel" style={{ maxHeight: 340, overflowY: "auto" }}>
          <PanelHeader
            title="Dataset Tree"
            icon="folder"
            sub={tree ? "datasets/normalized/" : "Click preview to browse"}
          />
          <div style={{ padding: "8px 6px" }}>
            {tree ? (
              <FileTree
                node={tree}
                onSelect={setSelectedFile}
                selected={selectedFile?.name}
              />
            ) : (
              <div
                style={{ padding: 24, textAlign: "center", color: T.muted, fontSize: 12 }}
              >
                Click the panel on the left to preview
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Run buttons */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          className="btn btn-primary"
          style={{ padding: "10px 24px" }}
          disabled={!apiOnline}
          onClick={() => onStartRun("full")}
        >
          <Icon name="play" size={13} /> Run Full Pipeline
        </button>
        <button
          className="btn btn-ghost"
          disabled={!apiOnline}
          onClick={() => onStartRun("validate")}
        >
          <Icon name="validate" size={13} /> Validate Only
        </button>
        <button
          className="btn btn-ghost"
          disabled={!apiOnline}
          onClick={() => onStartRun("gaps")}
        >
          <Icon name="scope" size={13} /> Gap Analysis Only
        </button>
        <button
          className="btn btn-ghost"
          disabled={!apiOnline}
          onClick={() => onStartRun("atlas")}
        >
          <Icon name="layers" size={13} /> Constraint Atlas Only
        </button>
      </div>

      {!apiOnline && (
        <div style={{ marginTop: 10, fontSize: 11, color: T.amber }}>
          ⚠ Start the API server first:{" "}
          <span style={{ fontFamily: T.mono }}>
            cd ~/spindep_framework &amp;&amp; python3 app_server.py
          </span>
        </div>
      )}
    </div>
  );
};