// Small API client: same-origin fetch, typed JSON, explicit HTTP errors.

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function detailFromBody(body: unknown): string | null {
  if (typeof body !== 'object' || body === null || !('detail' in body)) {
    return null;
  }
  const detail = (body as { detail: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === 'object' && item !== null && 'msg' in item
          ? String((item as { msg: unknown }).msg)
          : 'Invalid input',
      )
      .join('; ');
  }
  return null;
}

async function errorMessage(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) return `Request failed (${response.status})`;
  try {
    return detailFromBody(JSON.parse(text)) ?? text;
  } catch {
    return text;
  }
}

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
