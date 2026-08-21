export type ApiErrorBody = {
  error?: { code?: string; message?: string; request_id?: string; retryable?: boolean };
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  request_id?: string;
};

export class FDEMasteryApiError extends Error {
  constructor(public readonly status: number, public readonly body: ApiErrorBody, public readonly requestId?: string) {
    super(`FDE Mastery API request failed with HTTP ${status}`);
    this.name = "FDEMasteryApiError";
  }
}

export interface FDEMasteryClientOptions {
  baseUrl: string;
  apiKey?: string;
  bearerToken?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export class FDEMasteryClient {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;

  constructor(options: FDEMasteryClientOptions) {
    const url = options.baseUrl.replace(/\/$/, "");
    if (!/^https:\/\//.test(url) && !/^http:\/\/(localhost|127\.0\.0\.1)(?::\d+)?$/.test(url)) {
      throw new Error("baseUrl must use HTTPS outside localhost");
    }
    if (options.apiKey && options.bearerToken) throw new Error("provide either apiKey or bearerToken");
    this.baseUrl = url;
    this.headers = {
      Accept: "application/json",
      "User-Agent": "fde-mastery-typescript/1.20",
      ...(options.apiKey ? { "X-API-Key": options.apiKey } : {}),
      ...(options.bearerToken ? { Authorization: `Bearer ${options.bearerToken}` } : {}),
    };
    this.timeoutMs = Math.min(Math.max(options.timeoutMs ?? 10_000, 100), 120_000);
    this.maxRetries = Math.min(Math.max(options.maxRetries ?? 2, 0), 5);
  }

  private async request<T>(path: string, init: RequestInit = {}, idempotencyKey?: string): Promise<T> {
    const method = (init.method ?? "GET").toUpperCase();
    if ((method === "POST" || method === "PATCH") && !idempotencyKey) {
      throw new Error("mutating requests require an idempotencyKey");
    }
    const headers = new Headers(this.headers);
    headers.set("X-Request-ID", crypto.randomUUID());
    if (idempotencyKey) headers.set("Idempotency-Key", idempotencyKey);
    if (init.body) headers.set("Content-Type", "application/json");

    let attempt = 0;
    while (true) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      try {
        const response = await fetch(`${this.baseUrl}${path}`, { ...init, method, headers, signal: controller.signal });
        const raw = await response.text();
        const body = raw ? (JSON.parse(raw) as T & ApiErrorBody) : (undefined as T);
        if (response.ok) return body as T;
        const retryable = [429, 502, 503, 504].includes(response.status);
        if (!retryable || attempt >= this.maxRetries || (method !== "GET" && !idempotencyKey)) {
          throw new FDEMasteryApiError(response.status, body as ApiErrorBody, response.headers.get("X-Request-ID") ?? undefined);
        }
        const retryAfter = Number(response.headers.get("Retry-After"));
        await new Promise((resolve) => setTimeout(resolve, Number.isFinite(retryAfter) && retryAfter >= 0 ? retryAfter * 1000 : Math.min(2 ** attempt * 1000, 8000)));
        attempt += 1;
      } finally {
        clearTimeout(timer);
      }
    }
  }

  health(): Promise<{ status: string; api_version: string }> {
    return this.request("/v1/health");
  }

  capabilities(): Promise<Record<string, unknown>> {
    return this.request("/v1/capabilities");
  }

  triage(clientId: string, domain: string, payload: Record<string, unknown>, idempotencyKey: string): Promise<Record<string, unknown>> {
    if (!clientId || !domain || !idempotencyKey) throw new Error("clientId, domain and idempotencyKey are required");
    return this.request(`/v1/triage/${encodeURIComponent(clientId)}/${encodeURIComponent(domain)}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }, idempotencyKey);
  }
}
