import { describe, expect, it } from "vitest";

import { compareVersions } from "@/services/updater";

describe("compareVersions", () => {
  it("主版本号比较", () => {
    expect(compareVersions("2.0.0", "1.9.9")).toBe(1);
    expect(compareVersions("1.0.0", "2.0.0")).toBe(-1);
  });

  it("次版本号与补丁号比较", () => {
    expect(compareVersions("1.2.1", "1.2.0")).toBe(1);
    expect(compareVersions("1.2.3", "1.2.10")).toBe(-1);
  });

  it("忽略 v 前缀", () => {
    expect(compareVersions("v1.2.0", "1.2.0")).toBe(0);
  });

  it("预发布版本按数字段比较", () => {
    // dev 后缀拆成 0 参与，同版本号时 dev < 正式版
    expect(compareVersions("1.2.0-dev.1", "1.2.0")).toBe(-1);
    expect(compareVersions("1.2.1-dev.1", "1.2.0")).toBe(1);
  });

  it("段数不同时按缺失段补零", () => {
    expect(compareVersions("1.2", "1.2.0")).toBe(0);
    expect(compareVersions("1.3", "1.2.9")).toBe(1);
  });
});
