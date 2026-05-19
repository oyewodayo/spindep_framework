import { API_BASE_URL } from "../constants";
import type {
  PipelineMode,
  PipelineJob,
  PipelineResults,
  FileTreeNode,
  ApiStatus,
} from "../types";

// ─── Generic Fetcher ──────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText} — ${path}`);
  }
  return res.json() as Promise<T>;
}

// ─── Endpoints ────────────────────────────────────────────────────────────────

export const apiClient = {
  /**
   * Submit a new pipeline job.
   */
  run(mode: PipelineMode = "full"): Promise<{ job_id: string }> {
    return request(`/api/run?mode=${mode}`, { method: "POST" });
  },

  /**
   * Poll job status and log lines.
   */
  pollJob(jobId: string): Promise<PipelineJob> {
    return request(`/api/job/${jobId}`);
  },

  /**
   * Fetch final results once a job is done.
   */
  getResults(jobId: string): Promise<PipelineResults> {
    return request(`/api/results/${jobId}`);
  },

  /**
   * Lightweight health check — returns null on network failure.
   */
  async getStatus(): Promise<ApiStatus | null> {
    try {
      return await request<ApiStatus>("/api/status");
    } catch {
      return null;
    }
  },

  /**
   * Fetch the server-side dataset directory tree.
   */
  async getTree(): Promise<FileTreeNode> {
    return request<FileTreeNode>("/api/tree");
  },
};