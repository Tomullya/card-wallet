// Typed client for the Wallet API. Every call goes to /api/v1 on the same origin.

export interface ErrorDetail {
  field: string;
  problem: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: ErrorDetail[],
  ) {
    super(message);
  }
}

const TOKEN_KEY = "cw.token";
let onUnauthorized: () => void = () => {};

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
}

export function setUnauthorizedHandler(fn: () => void): void {
  onUnauthorized = fn;
}

export async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const token = getToken();
  const response = await fetch(`/api/v1${path}`, {
    method,
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const error = data?.error ?? {};
    if (response.status === 401 && token) onUnauthorized();
    throw new ApiError(
      response.status,
      error.code ?? "HTTP_ERROR",
      error.message ?? `Request failed (${response.status})`,
      error.details,
    );
  }
  return data as T;
}

// --- API shapes (see docs/api-guide.ru.md) ---

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface Account {
  id: string;
  currency: string;
  balance: string;
  created_at: string;
}

export interface Card {
  id: string;
  account_id: string;
  masked_pan: string;
  expiry: string;
  status: "ACTIVE" | "BLOCKED" | "EXPIRED";
  block_reason: string | null;
  daily_limit: string;
}

export interface IssuedCard {
  id: string;
  account_id: string;
  pan: string;
  cvv: string;
  expiry: string;
  status: string;
  daily_limit: string;
}

export interface Transaction {
  id: string;
  type: "TOP_UP" | "PAYMENT" | "COMMISSION";
  amount: string;
  currency: string;
  status: "APPROVED" | "DECLINED";
  decline_reason: string | null;
  merchant_name: string | null;
  card_last4: string | null;
  created_at: string;
}

export interface Statement {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface Payment {
  transaction_id: string;
  status: "APPROVED" | "DECLINED";
  decline_reason: string | null;
  amount: string;
  commission: string | null;
  currency: string;
  created_at: string;
}
