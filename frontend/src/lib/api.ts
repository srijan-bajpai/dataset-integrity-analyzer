import {
  DatasetListSchema,
  DatasetSchema,
  DatasetDetailSchema,
  RunSchema,
  ReportSchema,
  WhatIfResponseSchema,
  FlaggedSamplesListSchema,
  Embeddings3DSchema,
  RunComparisonSchema,
} from './schemas';
import type {
  Dataset,
  DatasetDetail,
  AnalysisRun,
  ReportData,
  WhatIfResponse,
  FlaggedSampleItem,
  Embeddings3DResponse,
  RunComparison,
} from './types';

export class ApiError extends Error {
  constructor(public status: number, message: string, public details?: unknown) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private getHeaders(password?: string | null): HeadersInit {
    const headers: HeadersInit = {
      'Accept': 'application/json',
    };
    if (password) {
      headers['X-DIA-Password'] = password;
    }
    return headers;
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
      let message = `API request failed with status ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          message = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        const text = await res.text();
        if (text) message = text;
      }
      throw new ApiError(res.status, message);
    }
    return res.json() as Promise<T>;
  }

  // --- Datasets ---
  async getDatasets(password?: string | null): Promise<Dataset[]> {
    const res = await fetch('/v1/datasets', {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return DatasetListSchema.parse(data) as Dataset[];
  }

  async verifyPassword(password: string): Promise<boolean> {
    try {
      const res = await fetch('/v1/datasets', {
        headers: this.getHeaders(password),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async getDataset(id: string, password?: string | null): Promise<DatasetDetail> {
    const res = await fetch(`/v1/datasets/${encodeURIComponent(id)}`, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return DatasetDetailSchema.parse(data) as DatasetDetail;
  }

  async uploadDataset(file: File, name?: string, password?: string | null): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    let url = '/v1/datasets';
    if (name) {
      url += `?name=${encodeURIComponent(name)}`;
    }
    const headers: HeadersInit = {};
    if (password) {
      headers['X-DIA-Password'] = password;
    }
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });
    const data = await this.handleResponse<unknown>(res);
    return DatasetSchema.parse(data) as Dataset;
  }

  async deleteDataset(id: string, password?: string | null): Promise<void> {
    const res = await fetch(`/v1/datasets/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: this.getHeaders(password),
    });
    if (!res.ok) {
      throw new ApiError(res.status, `Failed to delete dataset: ${res.statusText}`);
    }
  }

  // --- Runs ---
  async createRun(
    datasetId: string,
    config: {
      fairness_targets?: Record<string, Record<string, number>>;
      sampling_rate?: number;
      sampling_seed?: number;
      estimate_attributes?: boolean;
      predict_impact?: boolean;
    } = {},
    password?: string | null
  ): Promise<{ run_id: string; status: string; status_url: string }> {
    const headers = {
      ...this.getHeaders(password),
      'Content-Type': 'application/json',
    };
    const res = await fetch(`/v1/datasets/${encodeURIComponent(datasetId)}/runs`, {
      method: 'POST',
      headers,
      body: JSON.stringify(config),
    });
    return this.handleResponse(res);
  }

  async getRun(runId: string, password?: string | null): Promise<AnalysisRun> {
    const res = await fetch(`/v1/runs/${encodeURIComponent(runId)}`, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return RunSchema.parse(data) as AnalysisRun;
  }

  async cancelRun(runId: string, password?: string | null): Promise<{ run_id: string; status: string }> {
    const res = await fetch(`/v1/runs/${encodeURIComponent(runId)}/cancel`, {
      method: 'POST',
      headers: this.getHeaders(password),
    });
    return this.handleResponse(res);
  }

  // --- Reports & Visualizations ---
  async getReport(runId: string, password?: string | null): Promise<ReportData> {
    const res = await fetch(`/v1/runs/${encodeURIComponent(runId)}/report`, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return ReportSchema.parse(data) as unknown as ReportData;
  }

  async getWhatIf(
    runId: string,
    changes: Record<string, number>,
    password?: string | null
  ): Promise<WhatIfResponse> {
    const headers = {
      ...this.getHeaders(password),
      'Content-Type': 'application/json',
    };
    const res = await fetch(`/v1/runs/${encodeURIComponent(runId)}/what-if`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ changes }),
    });
    const data = await this.handleResponse<unknown>(res);
    return WhatIfResponseSchema.parse(data) as WhatIfResponse;
  }

  async getFlaggedSamples(
    runId: string,
    limit = 100,
    offset = 0,
    flaggedOnly = true,
    password?: string | null
  ): Promise<{ total: number; items: FlaggedSampleItem[] }> {
    const url = `/v1/runs/${encodeURIComponent(runId)}/samples?limit=${limit}&offset=${offset}&flagged_only=${flaggedOnly}`;
    const res = await fetch(url, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return FlaggedSamplesListSchema.parse(data) as { total: number; items: FlaggedSampleItem[] };
  }

  async getEmbeddings3D(runId: string, password?: string | null): Promise<Embeddings3DResponse> {
    const res = await fetch(`/v1/runs/${encodeURIComponent(runId)}/embeddings-3d`, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return Embeddings3DSchema.parse(data) as Embeddings3DResponse;
  }

  async compareRuns(runA: string, runB: string, password?: string | null): Promise<RunComparison> {
    const res = await fetch(`/v1/runs/${encodeURIComponent(runA)}/compare/${encodeURIComponent(runB)}`, {
      headers: this.getHeaders(password),
    });
    const data = await this.handleResponse<unknown>(res);
    return RunComparisonSchema.parse(data) as RunComparison;
  }

  // --- Sample Image URL ---
  getSampleImageUrl(datasetId: string, sampleRef: string, password?: string | null): string {
    const base = `/v1/datasets/${encodeURIComponent(datasetId)}/samples/${encodeURIComponent(sampleRef)}/image`;
    return password ? `${base}?token=${encodeURIComponent(password)}` : base;
  }

  // --- Direct Download Links ---
  getExportUrl(runId: string, type: 'html' | 'datasheet_md' | 'datasheet_json' | 'manifest_csv' | 'manifest_json' | 'samples_csv', password?: string | null): string {
    let path = '';
    switch (type) {
      case 'html': path = `/v1/runs/${runId}/report.html`; break;
      case 'datasheet_md': path = `/v1/runs/${runId}/model-card.md`; break;
      case 'datasheet_json': path = `/v1/runs/${runId}/model-card.json`; break;
      case 'manifest_csv': path = `/v1/runs/${runId}/remediation-manifest.csv`; break;
      case 'manifest_json': path = `/v1/runs/${runId}/remediation-manifest.json`; break;
      case 'samples_csv': path = `/v1/runs/${runId}/samples.csv`; break;
    }
    return password ? `${path}?token=${encodeURIComponent(password)}` : path;
  }
}

export const api = new ApiClient();
