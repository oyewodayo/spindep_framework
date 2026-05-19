import { useState, useEffect, useCallback, useRef } from "react";
import { apiClient } from "../api/client";
import { API_HEALTH_INTERVAL_MS, API_POLL_INTERVAL_MS } from "../constants";
import { estimateProgress } from "../utils";
import type { AnalysisPair, JobStatus, PipelineMode } from "../types";

// ─── useApiHealth ──────────────────────────────────────────────────────────────

export function useApiHealth(): boolean {
  const [online, setOnline] = useState(false);

  useEffect(() => {
    const check = async () => setOnline(!!(await apiClient.getStatus()));
    check();
    const id = setInterval(check, API_HEALTH_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  return online;
}

// ─── usePipelineJob ────────────────────────────────────────────────────────────

interface UsePipelineJobReturn {
  log: string[];
  progress: number;
  status: JobStatus;
}

export function usePipelineJob(
  jobId: string | null,
  onComplete?: () => void
): UsePipelineJobReturn {
  const [log, setLog]           = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus]     = useState<JobStatus>("queued");
  const cancelRef               = useRef(false);

  useEffect(() => {
    if (!jobId) return;
    cancelRef.current = false;

    const poll = async () => {
      while (!cancelRef.current) {
        try {
          const job = await apiClient.pollJob(jobId);
          if (cancelRef.current) break;

          setLog(job.log ?? []);
          setProgress(estimateProgress(job.log?.length ?? 0));

          if (job.status === "done") {
            setProgress(100);
            setStatus("done");
            setTimeout(() => onComplete?.(), 600);
            return;
          }
          if (job.status === "error") {
            setStatus("error");
            return;
          }
        } catch {
          // Network blip — keep polling
        }
        await new Promise(r => setTimeout(r, API_POLL_INTERVAL_MS));
      }
    };

    poll();
    return () => { cancelRef.current = true; };
  }, [jobId, onComplete]);

  return { log, progress, status };
}

// ─── usePipeline ───────────────────────────────────────────────────────────────

interface UsePipelineReturn {
  jobId: string | null;
  mode: PipelineMode;
  pairs: AnalysisPair[];
  resultsReady: boolean;
  startRun: (mode: PipelineMode) => Promise<void>;
  handleComplete: () => Promise<void>;
}

export function usePipeline(): UsePipelineReturn {
  const [jobId, setJobId]               = useState<string | null>(null);
  const [mode, setMode]                 = useState<PipelineMode>("full");
  const [pairs, setPairs]               = useState<AnalysisPair[]>([]);
  const [resultsReady, setResultsReady] = useState(false);

  const startRun = useCallback(async (m: PipelineMode) => {
    setMode(m);
    try {
      const { job_id } = await apiClient.run(m);
      setJobId(job_id);
    } catch {
      console.error("Could not reach API — is app_server.py running on port 8001?");
    }
  }, []);

  const handleComplete = useCallback(async () => {
    if (!jobId) return;
    try {
      const data = await apiClient.getResults(jobId);
      if (data?.pairs?.length) {
        setPairs(data.pairs);
        setResultsReady(true);
      }
    } catch (e) {
      console.error("Failed to fetch results:", e);
    }
  }, [jobId]);

  return { jobId, mode, pairs, resultsReady, startRun, handleComplete };
}

// ─── useSort ──────────────────────────────────────────────────────────────────

export function useSort<T>(defaultKey: keyof T, defaultDir: "asc" | "desc" = "asc") {
  const [sort, setSort] = useState<{ key: keyof T; direction: "asc" | "desc" }>({
    key: defaultKey,
    direction: defaultDir,
  });

  const toggleSort = useCallback((key: keyof T) => {
    setSort(prev =>
      prev.key === key
        ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" }
    );
  }, []);

  return { sort, toggleSort };
}

// ─── useCopyToClipboard ────────────────────────────────────────────────────────

export function useCopyToClipboard(resetDelay = 1_600) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copy = useCallback((key: string, text: string) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), resetDelay);
  }, [resetDelay]);

  return { copiedKey, copy };
}