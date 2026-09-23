/** 统一 fetch 客户端：JSON 序列化、错误归一化（HTTP 状态码 → ApiError）。 */

/** API 基地址：Tauri 下跨域直连后端，其余场景同源（Vite 代理 / FastAPI 托管）。
 * 与 usePlatform 解耦，避免循环依赖。
 */
function detectBase(): string {
  const tauri =
    typeof window !== "undefined" &&
    ((window as any).__TAURI_INTERNALS__ !== undefined ||
      (window as any).__TAURI__ !== undefined ||
      navigator.userAgent.includes("Tauri"));
  return tauri ? "http://127.0.0.1:5000" : "";
}

export const API_BASE = detectBase();

/** 拼接 API 地址（SSE 等需要完整 URL 的场景使用） */
export function apiUrl(path: string): string {
  return API_BASE + path;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (data && typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      // FastAPI 校验错误数组
      const first = data.detail[0];
      return first?.msg ? `参数错误: ${first.msg}` : "请求参数不合法";
    }
  } catch {
    // 非 JSON 响应（如后端未启动时的代理错误页）
  }
  if (response.status === 404) return "接口不存在";
  if (response.status >= 500) return "服务器内部错误";
  return `请求失败 (HTTP ${response.status})`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (e) {
    throw new ApiError(0, "无法连接到后端服务，请确认 LoArchive 正在运行");
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as T;
}

export function httpGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function httpPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });
}

export function httpDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}
