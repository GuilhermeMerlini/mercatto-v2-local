import { getToken } from "./token";

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
  }
}

const callbacks: Array<() => void> = [];

export function onUnauthorized(cb: () => void): () => void {
  callbacks.push(cb);
  return () => {
    const i = callbacks.indexOf(cb);
    if (i >= 0) callbacks.splice(i, 1);
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get("content-type");
  let data: unknown = undefined;

  if (contentType && contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch {
      // Se falhar ao parsear JSON, continua com data = undefined
    }
  }

  let detail: string;

  if (typeof data === "object" && data !== null && "detail" in data) {
    const detailData = (data as any).detail;
    if (Array.isArray(detailData)) {
      detail = detailData.map((e: any) => e.msg).join("; ");
    } else if (typeof detailData === "string") {
      detail = detailData;
    } else {
      detail = `Erro ${response.status}`;
    }
  } else {
    detail = `Erro ${response.status}`;
  }

  if (!response.ok) {
    if (response.status === 401) {
      callbacks.forEach(cb => cb());
    }
    throw new ApiError(response.status, detail);
  }

  return data as T;
}

export async function api<T>(
  path: string,
  init?: { method?: string; body?: unknown; headers?: Record<string, string> }
): Promise<T> {
  const url = (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + path;

  const method = init?.method ?? "GET";
  const headers: Record<string, string> = {};
  if (init?.headers) {
    Object.assign(headers, init.headers);
  }

  let body: string | undefined = undefined;
  if (init?.body !== undefined) {
    body = JSON.stringify(init.body);
    headers["Content-Type"] = "application/json";
  }

  const options: RequestInit = {
    method,
    headers,
    body,
  };

  const token = getToken();
  if (token) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    };
  }

  const response = await fetch(url, options);
  return handleResponse<T>(response);
}
