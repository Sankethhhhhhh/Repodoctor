import type {
  AnalyzeRequest,
  ReportListResponse,
  ReportResponse,
  CompareRequest,
  CompareResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const body = await response.json();
      message = body.error?.message ?? message;
    } catch {
      /* non-JSON error page */
    }
    throw new Error(message);
  }
  return response.json();
}

export async function getHealth(): Promise<{
  status: string;
  version: string;
}> {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function analyzeRepo(url: string): Promise<ReportResponse> {
  const body: AnalyzeRequest = { url };
  return request<ReportResponse>("/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function getReport(id: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/reports/${id}`);
}

export async function listReports(): Promise<ReportListResponse> {
  return request<ReportListResponse>("/reports");
}

export async function compareReports(
  data: CompareRequest,
): Promise<CompareResponse> {
  return request<CompareResponse>("/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function exportUrl(
  reportId: string,
  format: "md" | "html" | "csv" | "pdf" | "sarif",
): string {
  return `${API_BASE}/reports/${reportId}/export/${format}`;
}
