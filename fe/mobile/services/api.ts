import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { ApiEnvelope, AuthDataType, LoginData, LoginPayload, Metadata, PredictionData, RegisterPayload, StatusData } from './type';

type RawPrediction = {
  presence: string;
  confidence: number;
  probability?: Record<string, number>;
  probabilities?: Record<string, number>;
  timestamp?: string;
};

type PredictRequest = {
  window: number[][];
};

const BACKEND_PORT = 8000;
const DEFAULT_API_BASE_URL = `http://127.0.0.1:${BACKEND_PORT}/api`;

function stripTrailingSlash(value: string): string {
  return value.replace(/\/$/, '');
}

function ensureApiPrefix(value: string): string {
  const normalized = stripTrailingSlash(value);
  return normalized.endsWith('/api') ? normalized : `${normalized}/api`;
}

function extractHostname(candidate: string | undefined): string | null {
  if (!candidate) {
    return null;
  }

  const withoutScheme = candidate.replace(/^https?:\/\//, '').replace(/^exp(s)?:\/\//, '');
  const hostPart = withoutScheme.split('/')[0];
  const hostname = hostPart.split(':')[0];

  return hostname || null;
}

function resolveApiBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (envUrl) {
    return ensureApiPrefix(envUrl);
  }

  const extraUrl = (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)?.apiBaseUrl?.trim();
  if (extraUrl) {
    return ensureApiPrefix(extraUrl);
  }

  const constants = Constants as typeof Constants & {
    expoGoConfig?: { debuggerHost?: string };
    manifest2?: { extra?: { devServer?: { hostUri?: string } } };
    manifest?: { debuggerHost?: string };
  };

  const hostCandidate =
    constants.expoGoConfig?.debuggerHost ||
    constants.expoConfig?.hostUri ||
    constants.manifest2?.extra?.devServer?.hostUri ||
    constants.manifest?.debuggerHost;

  const hostname = extractHostname(hostCandidate);
  if (hostname) {
    return `http://${hostname}:${BACKEND_PORT}/api`;
  }

  return DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = resolveApiBaseUrl();

const REQUEST_TIMEOUT_MS = 8000;
const ENABLE_API_DEBUG_LOG = true;

function debugApiLog(label: string, payload?: unknown) {
  if (!ENABLE_API_DEBUG_LOG) return;
  if (payload === undefined) {
    console.log(label);
    return;
  }
  console.log(label, payload);
}

function toDebugError(error: unknown) {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
    };
  }
  return { message: String(error) };
}

function normalizePrediction(item: RawPrediction): PredictionData {
  return {
    presence: item.presence,
    confidence: item.confidence,
    probabilities: item.probabilities ?? item.probability ?? {},
    timestamp: item.timestamp ?? new Date().toISOString(),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await AsyncStorage.getItem('accessToken');
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const method = (init?.method ?? 'GET').toUpperCase();
  const url = `${API_BASE_URL}${path}`;
  const startedAt = Date.now();

  debugApiLog(`[API REQUEST] ${method} ${url}`, {
    hasToken: Boolean(token),
    body: init?.body ?? null,
  });

  try {
    const response = await fetch(url, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers ?? {}),
      },
    });

    clearTimeout(timeoutId);

    const raw = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;

    debugApiLog(`[API RESPONSE] ${method} ${url}`, {
      status: response.status,
      ok: response.ok,
      durationMs: Date.now() - startedAt,
      body: raw,
    });

    if (!response.ok) {
      const errorMessage =
        raw?.detail ||
        raw?.message ||
        `Request failed (${response.status})`;
      throw new Error(errorMessage);
    }

    if (raw && raw.success === false) {
      throw new Error(raw.message || 'Yêu cầu không thành công');
    }

    // Nếu backend trả về theo ApiEnvelope
    if (raw && typeof raw === 'object' && 'data' in raw) {
      return raw.data as T;
    }

    // Nếu backend trả về thẳng object data
    return raw as T;
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    debugApiLog(`[API ERROR] ${method} ${url}`, {
      durationMs: Date.now() - startedAt,
      error: toDebugError(error),
    });

    const err = error as { name?: string; message?: string };

    if (err?.name === 'AbortError') {
      throw new Error(`Hết thời gian chờ API sau ${REQUEST_TIMEOUT_MS / 1000}s (${API_BASE_URL})`);
    }

    if (error instanceof Error && err.message && !/Network request failed/i.test(err.message)) {
      throw error;
    }

    throw new Error(
      `Không kết nối được backend tại ${API_BASE_URL}. Kiểm tra:\n` +
      `1) Backend đang chạy trên máy local\n` +
      `2) Điện thoại và máy tính đang cùng Wi-Fi\n` +
      `3) Địa chỉ backend là IP LAN của máy tính, không phải localhost\n` +
      `4) Nếu cần, set EXPO_PUBLIC_API_BASE_URL hoặc app.json extra.apiBaseUrl\n` +
      `5) Firewall không chặn cổng ${BACKEND_PORT}`
    );
  }
}

export const api = {
  getStatus: () => request<StatusData>('/status'),

  getLatest: async () =>
    normalizePrediction(await request<RawPrediction>('/latest')),

  predict: async (window: number[][]) =>
    normalizePrediction(
      await request<RawPrediction>('/predict', {
        method: 'POST',
        body: JSON.stringify({ window } as PredictRequest),
      }),
    ),

  getMe: () => request<Metadata>('/auth/user/me'),

  getHistory: async (limit = 100) => {
    const rows = await request<RawPrediction[]>(`/history?limit=${limit}`);
    return rows.map(normalizePrediction);
  },

  startMonitoring: () =>
    request<unknown>('/control/start', {
      method: 'POST',
    }),

  stopMonitoring: () =>
    request<unknown>('/control/stop', {
      method: 'POST',
    }),

  register: (payload: RegisterPayload) =>
    request<AuthDataType>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: async (payload: LoginPayload): Promise<AuthDataType> => {
    const res = await request<LoginData>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    await AsyncStorage.setItem('accessToken', res.access_token);

    return {
      user_id: res.user_id,
      email: res.email,
    };
  },

  logout: async () => {
    await AsyncStorage.removeItem('accessToken');
  },
};