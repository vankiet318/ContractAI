import { AUTH_UNAUTHORIZED_EVENT } from "../constants";
import { clearToken, getToken } from "./authStorage";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

const NETWORK_ERROR_MESSAGE =
  "Không kết nối được máy chủ. Vui lòng kiểm tra kết nối và thử lại.";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function withAuthHeaders(init?: RequestInit): RequestInit {
  const headers = new Headers(init?.headers);
  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return { ...init, headers };
}

async function handleUnauthorized(response: Response) {
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
  }
}

async function throwApiError(response: Response): Promise<never> {
  await handleUnauthorized(response);

  const body = await response.json().catch(() => null);
  throw new ApiError(
    readErrorDetail(body?.detail) ?? statusErrorMessage(response.status),
    response.status,
  );
}

function statusErrorMessage(status: number): string {
  return `Có lỗi xảy ra (mã ${status}). Vui lòng thử lại.`;
}

/** Message for any caught error: the server's message when there is one,
 * otherwise the caller's fallback. */
export function toErrorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

// fetch rejects (instead of returning a response) when the server is
// unreachable; turn that into an ApiError so callers handle one type.
async function send(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, withAuthHeaders(init));
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, 0);
  }
}

// FastAPI validation errors (422) send a list of {msg, ...} instead of a
// string; show the first message rather than "[object Object]".
function readErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
    return detail[0].msg.replace(/^Value error, /, "");
  }

  return undefined;
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await send(path, init);

  if (!response.ok) {
    await throwApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function requestBlob(
  path: string,
  init?: RequestInit,
): Promise<Blob> {
  const response = await send(path, init);

  if (!response.ok) {
    await handleUnauthorized(response);
    throw new ApiError(statusErrorMessage(response.status), response.status);
  }

  return response.blob();
}

const EVENT_SEPARATOR = "\n\n";

export interface ServerSentEvent {
  event: string;
  data: string;
}

// EventSource cannot send the Authorization header, so the stream is
// read from fetch and split into events on blank lines.
async function requestEventStream(
  path: string,
  init: RequestInit,
  onEvent: (event: ServerSentEvent) => void,
): Promise<void> {
  const response = await send(path, init);

  if (!response.ok) {
    await throwApiError(response);
  }

  if (!response.body) {
    throw new ApiError("Streaming is not supported", response.status);
  }

  const reader = response.body
    .pipeThrough(new TextDecoderStream())
    .getReader();

  let buffer = "";

  for (;;) {
    const { value, done } = await readStreamChunk(reader);
    if (done) return;

    buffer += value;

    let boundary = buffer.indexOf(EVENT_SEPARATOR);

    while (boundary >= 0) {
      onEvent(parseServerSentEvent(buffer.slice(0, boundary)));
      buffer = buffer.slice(boundary + EVENT_SEPARATOR.length);
      boundary = buffer.indexOf(EVENT_SEPARATOR);
    }
  }
}

async function readStreamChunk(
  reader: ReadableStreamDefaultReader<string>,
): Promise<ReadableStreamReadResult<string>> {
  try {
    return await reader.read();
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, 0);
  }
}

function parseServerSentEvent(raw: string): ServerSentEvent {
  const event: ServerSentEvent = { event: "message", data: "" };
  const dataLines: string[] = [];

  for (const line of raw.split("\n")) {
    if (line.startsWith("event: ")) event.event = line.slice(7);
    if (line.startsWith("data: ")) dataLines.push(line.slice(6));
  }

  event.data = dataLines.join("\n");

  return event;
}

export const apiClient = { request, requestBlob, requestEventStream };
