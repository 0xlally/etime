import { Capacitor } from '@capacitor/core';

export type OfflineTimerStatus = 'running' | 'ended' | 'synced' | 'failed';
export type OfflineTimerSource = 'web' | 'android';

export interface OfflineTimerRecord {
  local_timer_id: string;
  category_id?: number;
  started_at: string;
  ended_at?: string;
  note?: string;
  status: OfflineTimerStatus;
  source: OfflineTimerSource;
  created_offline: boolean;
  multiplier?: number;
  server_session_id?: number;
  client_generated_id?: string;
  synced_session_id?: number;
  last_error?: string;
  template_id?: number;
  template_duration_seconds?: number;
  template_completed_at?: string;
  updated_at: string;
}

export interface OfflineTimerSnapshot {
  pendingCount: number;
  failedCount: number;
  runningCount: number;
}

export interface OfflineTimerSyncResult extends OfflineTimerSnapshot {
  syncedCount: number;
  runningSynced: boolean;
}

interface TimerSyncClient {
  get<T>(url: string, params?: unknown): Promise<T>;
  post<T>(url: string, data?: unknown): Promise<T>;
}

interface ActiveSessionLike {
  id: number;
  category_id?: number | null;
  start_time: string;
  note?: string | null;
  elapsed_seconds?: number;
  client_generated_id?: string | null;
}

interface SessionResponseLike {
  id: number;
  end_time?: string | null;
  client_generated_id?: string | null;
}

const STORAGE_KEY = 'etime.offline.timer.records.v1';

const nowIso = () => new Date().toISOString();

const getStorage = (): Storage | null => {
  if (typeof window === 'undefined') return null;

  try {
    return window.localStorage;
  } catch {
    return null;
  }
};

const writeRecords = (records: OfflineTimerRecord[]) => {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(STORAGE_KEY, JSON.stringify(records));
};

const normalizeNumber = (value: unknown): number | undefined => (
  typeof value === 'number' && Number.isFinite(value) ? value : undefined
);

const normalizeRecord = (value: unknown): OfflineTimerRecord | null => {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Partial<OfflineTimerRecord>;
  if (typeof raw.local_timer_id !== 'string' || typeof raw.started_at !== 'string') return null;
  if (!['running', 'ended', 'synced', 'failed'].includes(String(raw.status))) return null;

  return {
    local_timer_id: raw.local_timer_id,
    category_id: normalizeNumber(raw.category_id),
    started_at: raw.started_at,
    ended_at: typeof raw.ended_at === 'string' ? raw.ended_at : undefined,
    note: typeof raw.note === 'string' ? raw.note : undefined,
    status: raw.status as OfflineTimerStatus,
    source: raw.source === 'android' ? 'android' : 'web',
    created_offline: Boolean(raw.created_offline),
    multiplier: normalizeNumber(raw.multiplier),
    server_session_id: normalizeNumber(raw.server_session_id),
    client_generated_id: typeof raw.client_generated_id === 'string' ? raw.client_generated_id : undefined,
    synced_session_id: normalizeNumber(raw.synced_session_id),
    last_error: typeof raw.last_error === 'string' ? raw.last_error : undefined,
    template_id: normalizeNumber(raw.template_id),
    template_duration_seconds: normalizeNumber(raw.template_duration_seconds),
    template_completed_at: typeof raw.template_completed_at === 'string' ? raw.template_completed_at : undefined,
    updated_at: typeof raw.updated_at === 'string' ? raw.updated_at : raw.started_at,
  };
};

export const getTimerSource = (): OfflineTimerSource => (
  Capacitor.isNativePlatform() ? 'android' : 'web'
);

export const isNetworkOnline = () => (
  typeof navigator === 'undefined' ? true : navigator.onLine
);

export const readOfflineTimerRecords = (): OfflineTimerRecord[] => {
  const storage = getStorage();
  if (!storage) return [];

  const raw = storage.getItem(STORAGE_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(normalizeRecord).filter((item): item is OfflineTimerRecord => item !== null);
  } catch {
    return [];
  }
};

export const createLocalTimerId = (source: OfflineTimerSource = getTimerSource()) => {
  const random = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `etime-${source}-${random}`;
};

export const calculateElapsedSeconds = (startedAt: string, nowMs = Date.now()) => {
  const startedMs = new Date(startedAt).getTime();
  if (!Number.isFinite(startedMs)) return 0;
  return Math.max(0, Math.floor((nowMs - startedMs) / 1000));
};

export const createRunningTimerRecord = (input: {
  categoryId?: number | null;
  note?: string | null;
  startedAt?: string;
  createdOffline?: boolean;
  serverSessionId?: number;
  clientGeneratedId?: string | null;
  templateId?: number;
  templateDurationSeconds?: number | null;
  templateCompletedAt?: string | null;
}): OfflineTimerRecord => {
  const source = getTimerSource();
  const localId = input.clientGeneratedId || (
    input.serverSessionId ? `server-${input.serverSessionId}` : createLocalTimerId(source)
  );

  return {
    local_timer_id: localId,
    category_id: input.categoryId ?? undefined,
    started_at: input.startedAt ?? nowIso(),
    note: input.note ?? undefined,
    status: 'running',
    source,
    created_offline: input.createdOffline ?? !isNetworkOnline(),
    server_session_id: input.serverSessionId,
    client_generated_id: input.clientGeneratedId ?? localId,
    template_id: input.templateId,
    template_duration_seconds: input.templateDurationSeconds ?? undefined,
    template_completed_at: input.templateCompletedAt ?? undefined,
    updated_at: nowIso(),
  };
};

export const saveRunningTimer = (record: OfflineTimerRecord) => {
  const updated = { ...record, status: 'running' as const, updated_at: nowIso() };
  const records = readOfflineTimerRecords()
    .filter((item) => item.local_timer_id !== record.local_timer_id && item.status !== 'running');
  writeRecords([...records, updated]);
  return updated;
};

export const upsertOfflineTimerRecord = (record: OfflineTimerRecord) => {
  const updated = { ...record, updated_at: nowIso() };
  const records = readOfflineTimerRecords();
  const existingIndex = records.findIndex((item) => item.local_timer_id === record.local_timer_id);

  if (existingIndex >= 0) {
    records[existingIndex] = updated;
  } else {
    records.push(updated);
  }

  writeRecords(records);
  return updated;
};

export const getRunningTimer = () => (
  readOfflineTimerRecords()
    .filter((record) => record.status === 'running')
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0] ?? null
);

export const finishRunningTimer = (
  localTimerId: string,
  input: { endedAt?: string; note?: string; multiplier?: number },
) => {
  const records = readOfflineTimerRecords();
  const index = records.findIndex((record) => record.local_timer_id === localTimerId);
  if (index < 0) return null;

  const existing = records[index];
  const ended: OfflineTimerRecord = {
    ...existing,
    ended_at: input.endedAt ?? nowIso(),
    note: input.note ?? existing.note,
    multiplier: input.multiplier,
    status: 'ended',
    updated_at: nowIso(),
  };
  records[index] = ended;
  writeRecords(records);
  return ended;
};

export const markTimerSynced = (localTimerId: string, sessionId?: number) => {
  const records = readOfflineTimerRecords()
    .filter((record) => record.local_timer_id !== localTimerId);
  writeRecords(records);

  return sessionId;
};

export const markTimerFailed = (localTimerId: string, error: string) => {
  const records = readOfflineTimerRecords();
  const index = records.findIndex((record) => record.local_timer_id === localTimerId);
  if (index < 0) return null;

  const failed: OfflineTimerRecord = {
    ...records[index],
    status: 'failed',
    last_error: error,
    updated_at: nowIso(),
  };
  records[index] = failed;
  writeRecords(records);
  return failed;
};

export const removeOfflineTimerRecord = (localTimerId: string) => {
  writeRecords(readOfflineTimerRecords().filter((record) => record.local_timer_id !== localTimerId));
};

export const getPendingTimers = () => (
  readOfflineTimerRecords().filter((record) => record.status === 'ended' || record.status === 'failed')
);

export const getOfflineTimerSnapshot = (): OfflineTimerSnapshot => {
  const records = readOfflineTimerRecords();
  return {
    pendingCount: records.filter((record) => record.status === 'ended' || record.status === 'failed').length,
    failedCount: records.filter((record) => record.status === 'failed').length,
    runningCount: records.filter((record) => record.status === 'running').length,
  };
};

export const buildManualSessionPayload = (record: OfflineTimerRecord) => {
  if (!record.ended_at) {
    throw new Error('ended_at is required to sync a completed offline timer');
  }

  return {
    category_id: record.category_id,
    start_time: record.started_at,
    end_time: record.ended_at,
    note: record.note,
    multiplier: record.multiplier,
    client_generated_id: record.client_generated_id ?? record.local_timer_id,
  };
};

export const buildStartSessionPayload = (record: OfflineTimerRecord) => ({
  category_id: record.category_id,
  note: record.note,
  started_at: record.started_at,
  client_generated_id: record.client_generated_id ?? record.local_timer_id,
});

export const markTemplateDurationCompleted = (localTimerId: string, completedAt = nowIso()) => {
  const records = readOfflineTimerRecords();
  const index = records.findIndex((record) => record.local_timer_id === localTimerId);
  if (index < 0) return null;

  const updated: OfflineTimerRecord = {
    ...records[index],
    template_completed_at: completedAt,
    updated_at: nowIso(),
  };
  records[index] = updated;
  writeRecords(records);
  return updated;
};

const getErrorMessage = (error: unknown) => {
  const apiError = error as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = apiError.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return apiError.message || '同步失败';
};

const loadActiveSession = async (client: TimerSyncClient) => {
  try {
    return await client.get<ActiveSessionLike | null>('/sessions/active');
  } catch {
    return null;
  }
};

const activeMatchesRecord = (active: ActiveSessionLike | null, record: OfflineTimerRecord) => {
  if (!active) return false;
  if (record.server_session_id && active.id === record.server_session_id) return true;
  return Boolean(record.client_generated_id && active.client_generated_id === record.client_generated_id);
};

const syncCompletedTimer = async (client: TimerSyncClient, record: OfflineTimerRecord) => {
  const active = await loadActiveSession(client);

  if (activeMatchesRecord(active, record)) {
    const stopped = await client.post<SessionResponseLike>('/sessions/stop', {
      note: record.note,
      multiplier: record.multiplier,
    });
    markTimerSynced(record.local_timer_id, stopped.id);
    return stopped;
  }

  if (record.server_session_id) {
    try {
      const existing = await client.get<SessionResponseLike>(`/sessions/${record.server_session_id}`);
      if (existing.end_time) {
        markTimerSynced(record.local_timer_id, existing.id);
        return existing;
      }
    } catch {
      const created = await client.post<SessionResponseLike>('/sessions/manual', buildManualSessionPayload(record));
      markTimerSynced(record.local_timer_id, created.id);
      return created;
    }

    throw new Error('服务端计时仍在进行，暂不覆盖');
  }

  const created = await client.post<SessionResponseLike>('/sessions/manual', buildManualSessionPayload(record));
  markTimerSynced(record.local_timer_id, created.id);
  return created;
};

const syncRunningTimer = async (client: TimerSyncClient, record: OfflineTimerRecord) => {
  if (record.server_session_id) return false;

  const active = await loadActiveSession(client);
  if (activeMatchesRecord(active, record)) {
    saveRunningTimer({
      ...record,
      server_session_id: active?.id,
      client_generated_id: active?.client_generated_id ?? record.client_generated_id,
      status: 'running',
    });
    return false;
  }

  if (active) {
    markTimerFailed(record.local_timer_id, '服务端已有正在计时，已优先保留服务端计时');
    return false;
  }

  const created = await client.post<SessionResponseLike>('/sessions/start', buildStartSessionPayload(record));
  saveRunningTimer({
    ...record,
    server_session_id: created.id,
    client_generated_id: created.client_generated_id ?? record.client_generated_id,
    status: 'running',
  });
  return true;
};

export const syncOfflineTimers = async (client: TimerSyncClient): Promise<OfflineTimerSyncResult> => {
  let syncedCount = 0;
  let failedDuringSync = 0;
  let runningSynced = false;

  if (!isNetworkOnline()) {
    return { ...getOfflineTimerSnapshot(), syncedCount, runningSynced };
  }

  const completed = getPendingTimers().filter((record) => Boolean(record.ended_at));
  for (const record of completed) {
    try {
      await syncCompletedTimer(client, record);
      syncedCount += 1;
    } catch (error) {
      markTimerFailed(record.local_timer_id, getErrorMessage(error));
      failedDuringSync += 1;
    }
  }

  const running = getRunningTimer()
    ?? readOfflineTimerRecords().find((record) => record.status === 'failed' && !record.ended_at)
    ?? null;
  if (running) {
    try {
      runningSynced = await syncRunningTimer(client, running);
    } catch (error) {
      markTimerFailed(running.local_timer_id, getErrorMessage(error));
      failedDuringSync += 1;
    }
  }

  const snapshot = getOfflineTimerSnapshot();
  return {
    ...snapshot,
    failedCount: Math.max(snapshot.failedCount, failedDuringSync),
    syncedCount,
    runningSynced,
  };
};
