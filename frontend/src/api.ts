import type {
  AuthResponse,
  AuthUser,
  QueryWorkflowRequest,
  QueryWorkflowResponse,
} from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

const ACCESS_TOKEN_KEY = "safequery.accessToken";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function saveAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function removeAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

function getErrorMessage(
  payload: unknown,
  status: number,
): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload
  ) {
    const detail = (payload as { detail: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (
      detail &&
      typeof detail === "object" &&
      "message" in detail
    ) {
      const message = (
        detail as { message: unknown }
      ).message;

      if (typeof message === "string") {
        return message;
      }
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            item &&
            typeof item === "object" &&
            "msg" in item
          ) {
            const message = (
              item as { msg: unknown }
            ).msg;

            return typeof message === "string"
              ? message
              : null;
          }

          return null;
        })
        .filter(
          (message): message is string =>
            message !== null,
        );

      if (messages.length > 0) {
        return messages.join(" ");
      }
    }
  }

  return `Request failed with status ${status}.`;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  authenticated = false,
): Promise<T> {
  const headers = new Headers(options.headers);

  if (
    options.body !== undefined &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (authenticated) {
    const token = getAccessToken();

    if (!token) {
      throw new Error(
        "Authentication is required.",
      );
    }

    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,
        headers,
      },
    );
  } catch {
    throw new Error(
      "Could not connect to the SafeQuery API. Confirm that the backend is running.",
    );
  }

  const payload: unknown = await response
    .json()
    .catch(() => null);

  if (!response.ok) {
    if (
      authenticated &&
      response.status === 401
    ) {
      removeAccessToken();

      window.dispatchEvent(
        new Event("safequery:unauthorized"),
      );
    }

    throw new Error(
      getErrorMessage(
        payload,
        response.status,
      ),
    );
  }

  return payload as T;
}

export async function signupUser(
  name: string,
  email: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>(
    "/v1/auth/signup",
    {
      method: "POST",
      body: JSON.stringify({
        name,
        email,
        password,
      }),
    },
  );
}

export async function loginUser(
  email: string,
  password: string,
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>(
    "/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    },
  );
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/v1/auth/me",
    {
      method: "GET",
    },
    true,
  );
}

export async function submitQuery(
  request: QueryWorkflowRequest,
): Promise<QueryWorkflowResponse> {
  return apiRequest<QueryWorkflowResponse>(
    "/v1/query",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
    true,
  );
}