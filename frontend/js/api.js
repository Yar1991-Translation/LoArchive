/* API基础地址 - Tauri环境需要完整URL */
export function getApiBase() {
  const isTauri =
    window.__TAURI__ !== undefined ||
    window.__TAURI_INTERNALS__ !== undefined ||
    navigator.userAgent.includes("Tauri");
  return isTauri ? "http://localhost:5000" : "";
}
const API_BASE = getApiBase();
