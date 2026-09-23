import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/api/client";

// client.ts 的模块级 API_BASE 探测依赖 window —— 在 jsdom 中默认非 Tauri，应为同源空串
describe("api client", () => {
  it("非 Tauri 环境使用同源基地址", async () => {
    const { API_BASE } = await import("@/api/client");
    expect(API_BASE).toBe("");
  });

  it("HTTP 错误归一化为 ApiError 并提取 detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "已有任务在运行中" }), {
          status: 409,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const { httpPost } = await import("@/api/client");
    const promise = httpPost("/api/task/start", {});
    await expect(promise).rejects.toMatchObject({
      status: 409,
      message: "已有任务在运行中",
    });
    vi.unstubAllGlobals();
  });

  it("FastAPI 校验错误数组转为可读信息", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: [{ loc: ["body", "mode"], msg: "Input should be 'like1'" }] }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const { httpPost } = await import("@/api/client");
    await expect(httpPost("/api/task/start", {})).rejects.toMatchObject({
      status: 422,
    });
    vi.unstubAllGlobals();
  });

  it("网络失败转为连接错误提示", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const { httpGet } = await import("@/api/client");
    const promise = httpGet("/api/version");
    await expect(promise).rejects.toMatchObject({
      status: 0,
      message: "无法连接到后端服务，请确认 LoArchive 正在运行",
    });
    vi.unstubAllGlobals();
  });

  it("ApiError 是 Error 的子类", () => {
    const err = new ApiError(404, "记录不存在");
    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(404);
  });
});
