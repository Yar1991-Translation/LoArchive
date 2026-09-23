/** 各域端点封装（路径与 docs/api.md 的 v2 契约一致）。 */

import { apiUrl, httpDelete, httpGet, httpPost } from "./client";
import type {
  AppSettings,
  AppConfig,
  HistoryCheckResult,
  HistoryQueryResult,
  TaskStatus,
} from "./types";

// ---------- 元信息 ----------

export function getVersion(): Promise<{ version: string }> {
  return httpGet("/api/version");
}

// ---------- 配置 / 设置 ----------

export function getConfig(): Promise<AppConfig> {
  return httpGet("/api/config");
}

export function saveConfig(payload: { login_key: string; login_auth: string }): Promise<{ message: string }> {
  return httpPost("/api/config", payload);
}

export function getSettings(): Promise<AppSettings> {
  return httpGet("/api/settings");
}

export function saveSettings(payload: Partial<AppSettings>): Promise<{ message: string }> {
  return httpPost("/api/settings", payload);
}

// ---------- 任务 ----------

export function startTask(type: string, params: Record<string, unknown>): Promise<{ message: string }> {
  return httpPost("/api/task/start", { type, params });
}

export function getTaskStatus(): Promise<TaskStatus> {
  return httpGet("/api/task/status");
}

export function stopTask(): Promise<{ message: string }> {
  return httpPost("/api/task/stop");
}

// ---------- 历史 ----------

export interface HistoryQueryOptions {
  page?: number;
  perPage?: number;
  type?: string;
  source?: string;
  search?: string;
}

export function queryHistory(options: HistoryQueryOptions = {}): Promise<HistoryQueryResult> {
  const params = new URLSearchParams();
  params.set("page", String(options.page ?? 1));
  params.set("per_page", String(options.perPage ?? 20));
  if (options.type) params.set("type", options.type);
  if (options.source) params.set("source", options.source);
  if (options.search) params.set("search", options.search);
  return httpGet(`/api/history?${params.toString()}`);
}

export function clearHistory(): Promise<{ message: string }> {
  return httpPost("/api/history/clear");
}

export function deleteHistoryItem(itemId: string): Promise<{ message: string }> {
  return httpDelete(`/api/history/delete/${encodeURIComponent(itemId)}`);
}

export function checkDownloaded(url: string): Promise<HistoryCheckResult> {
  return httpPost("/api/history/check", { url });
}

// ---------- 任务流（SSE） ----------

export function taskEventsUrl(): string {
  return apiUrl("/api/task/events");
}
