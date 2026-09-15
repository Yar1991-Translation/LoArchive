/* 任务事件流：优先 SSE 实时推送，连接失败时回退轮询 */
import { API_BASE } from "./api.js";

export function startTaskEventStream(handlers) {
  let doneReceived = false;
  let fallbackFired = false;
  const es = new EventSource(API_BASE + "/api/task/events");

  const parse = (e) => JSON.parse(e.data);

  es.addEventListener("snapshot", (e) => {
    if (handlers.onSnapshot) handlers.onSnapshot(parse(e));
  });
  es.addEventListener("log", (e) => {
    if (handlers.onLog) handlers.onLog(parse(e));
  });
  es.addEventListener("progress", (e) => {
    if (handlers.onProgress) handlers.onProgress(parse(e));
  });
  es.addEventListener("done", (e) => {
    doneReceived = true;
    es.close();
    if (handlers.onDone) handlers.onDone(parse(e));
  });
  es.addEventListener("ping", () => {});

  es.onerror = () => {
    es.close();
    if (!doneReceived && !fallbackFired) {
      fallbackFired = true;
      console.warn("SSE 连接失败，回退到轮询模式");
      if (handlers.onFallback) handlers.onFallback();
    }
  };

  return {
    close() {
      doneReceived = true;
      es.close();
    },
  };
}