/** 更新检查：GitHub Releases 最新版与本地版本比对（SemVer 语义的简化比较）。 */

import { h } from "vue";

import * as api from "@/api";
import { openExternal } from "@/composables/usePlatform";
import { notification } from "@/services/feedback";

const RELEASES_PAGE = "https://github.com/Yar1991-Translation/LoArchive/releases/latest";
const SKIP_KEY = "loarchive_update_skip";

interface GithubRelease {
  tag_name?: string;
  html_url?: string;
  body?: string;
}

interface ParsedVersion {
  nums: number[];
  /** 预发布段（如 "dev.1"），正式版为 null */
  pre: string | null;
}

function parseVersion(version: string): ParsedVersion {
  const cleaned = version.replace(/^v/, "");
  const dash = cleaned.indexOf("-");
  const core = dash === -1 ? cleaned : cleaned.slice(0, dash);
  const pre = dash === -1 ? null : cleaned.slice(dash + 1);
  return {
    nums: core.split(/[.+]/).map((part) => parseInt(part, 10) || 0),
    pre,
  };
}

/** a > b 返回 1，a < b 返回 -1，相等返回 0（SemVer 语义：预发布版 < 正式版） */
export function compareVersions(a: string, b: string): number {
  const pa = parseVersion(a);
  const pb = parseVersion(b);
  const length = Math.max(pa.nums.length, pb.nums.length);
  for (let i = 0; i < length; i++) {
    const diff = (pa.nums[i] ?? 0) - (pb.nums[i] ?? 0);
    if (diff !== 0) return diff > 0 ? 1 : -1;
  }
  // 数字段相同：正式版 > 预发布版
  if (pa.pre === null && pb.pre === null) return 0;
  if (pa.pre === null) return 1;
  if (pb.pre === null) return -1;
  // 都是预发布版：逐段比较，数字段按数值，其余按字典序
  const paParts = pa.pre.split(".");
  const pbParts = pb.pre.split(".");
  const preLength = Math.max(paParts.length, pbParts.length);
  for (let i = 0; i < preLength; i++) {
    const x = paParts[i];
    const y = pbParts[i];
    if (x === undefined) return -1;
    if (y === undefined) return 1;
    const xn = Number(x);
    const yn = Number(y);
    if (!Number.isNaN(xn) && !Number.isNaN(yn) && x !== "" && y !== "") {
      if (xn !== yn) return xn > yn ? 1 : -1;
    } else if (x !== y) {
      return x > y ? 1 : -1;
    }
  }
  return 0;
}

export async function fetchCurrentVersion(): Promise<string> {
  try {
    const { version } = await api.getVersion();
    return version;
  } catch {
    // 后端不可达时退回构建期注入的版本
    return __APP_VERSION__;
  }
}

export async function checkForUpdates(manual: boolean) {
  const currentVersion = await fetchCurrentVersion();
  let release: GithubRelease;
  try {
    const response = await fetch("https://api.github.com/repos/Yar1991-Translation/LoArchive/releases/latest");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    release = await response.json();
  } catch {
    if (manual) {
      notification.error({
        title: "检查更新失败",
        content: "无法访问 GitHub，请检查网络后重试",
        duration: 4000,
      });
    }
    return;
  }

  const latest = release.tag_name?.replace(/^v/, "") ?? "";
  if (latest && compareVersions(latest, currentVersion) > 0) {
    if (localStorage.getItem(SKIP_KEY) === latest) return;
    notification.create({
      title: `发现新版本 v${latest}`,
      content: `当前版本 v${currentVersion}，可前往下载页面获取`,
      duration: 0,
      action: () =>
        h("div", { style: "display:flex; gap:8px;" }, [
          h(
            "button",
            {
              style:
                "padding:4px 12px; cursor:pointer; border:1px solid var(--la-border); background:transparent; border-radius:6px;",
              onClick: () => {
                localStorage.setItem(SKIP_KEY, latest);
                notification.destroyAll();
              },
            },
            "忽略此版本",
          ),
          h(
            "button",
            {
              style:
                "padding:4px 12px; cursor:pointer; border:none; background:var(--la-primary); color:var(--la-primary-text); border-radius:6px;",
              onClick: () => openExternal(release.html_url ?? RELEASES_PAGE),
            },
            "前往下载",
          ),
        ]),
    });
  } else if (manual) {
    notification.success({
      title: "已是最新版本",
      content: `当前版本 v${currentVersion}`,
      duration: 4000,
    });
  }
}

/** 应用启动后延迟自动检查（不弹"已最新"提示） */
export function scheduleUpdateCheck() {
  window.setTimeout(() => {
    void checkForUpdates(false);
  }, 3000);
}
