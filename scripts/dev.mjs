/** 开发启动器：一条命令同时拉起 Python 后端与 Vite 前端。
 *
 * `npm run dev` 即可完成日常开发；`npm run tauri:dev` 通过 beforeDevCommand
 * 也会走到这里，桌面窗口与本地后端随之一键就绪。
 *
 * 行为：
 * - 后端退出（如 5000 端口被占用）时给出提示并继续保留前端；
 * - 前端退出或 Ctrl+C 时同时结束两端。
 */

import { spawn } from "node:child_process";

const children = { backend: null, frontend: null };
let shuttingDown = false;

function prefixPipe(child, name) {
  const tag = `[${name}] `;
  child.stdout?.setEncoding("utf8");
  child.stdout?.on("data", (chunk) => {
    process.stdout.write(
      chunk
        .split("\n")
        .filter((line) => line.length > 0)
        .map((line) => tag + line)
        .join("\n") + "\n",
    );
  });
  child.stderr?.setEncoding("utf8");
  child.stderr?.on("data", (chunk) => {
    process.stderr.write(
      chunk
        .split("\n")
        .filter((line) => line.length > 0)
        .map((line) => tag + line)
        .join("\n") + "\n",
    );
  });
}

function start(name, command, args) {
  // Windows 下经 shell 启动便于找到 python/npx；命令与参数拼成整串以避免
  // Node 24 对 "args + shell" 组合的弃用警告
  const child =
    process.platform === "win32"
      ? spawn([command, ...args].join(" "), { shell: true, stdio: ["ignore", "pipe", "pipe"] })
      : spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
  children[name] = child;
  prefixPipe(child, name);

  child.on("exit", (code) => {
    if (shuttingDown) return;
    if (name === "backend") {
      // 5000 被占用（后端已单独启动）或崩溃：提示后保留前端
      console.log(`[dev] 后端已退出（code=${code}）。若 5000 端口已被占用可忽略；否则请检查 Python 环境。`);
      children.backend = null;
    } else {
      console.log("[dev] 前端已退出，正在关闭后端…");
      shutdown(code ?? 0);
    }
  });
  return child;
}

function shutdown(exitCode) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of Object.values(children)) {
    if (!child || child.exitCode !== null) continue;
    if (process.platform === "win32") {
      // Windows 下需连同子进程树一起结束（python run.py / npm shell 包装）
      spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], { shell: false });
    } else {
      child.kill("SIGTERM");
    }
  }
  process.exit(exitCode);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

console.log("[dev] 启动后端 (python run.py) 与前端 (vite)…");
start("backend", "python", ["run.py"]);
start("frontend", "npx", ["vite"]);
