// 前端没有打包器，模块图错误只会在浏览器里表现为白屏。
// 这里静态校验 frontend/js 下每个具名导入都能在目标模块中找到对应导出。
//
// 用法：node scripts/check_esm.mjs
import fs from "node:fs";
import path from "node:path";

const dir = path.join(process.cwd(), "frontend", "js");
const files = fs.readdirSync(dir).filter((file) => file.endsWith(".js"));

function exportsOf(source) {
  const names = new Set();
  for (const match of source.matchAll(/export\s+(?:async\s+)?function\s+([A-Za-z0-9_$]+)/g)) names.add(match[1]);
  for (const match of source.matchAll(/export\s+(?:const|let|var)\s+([A-Za-z0-9_$]+)/g)) names.add(match[1]);
  for (const match of source.matchAll(/export\s*\{([^}]+)\}/g)) {
    for (const part of match[1].split(",")) {
      const name = part.trim().split(/\s+as\s+/).pop().trim();
      if (name) names.add(name);
    }
  }
  return names;
}

const sources = new Map();
for (const file of files) sources.set(file, fs.readFileSync(path.join(dir, file), "utf8"));

let problems = 0;
let checked = 0;

for (const [file, source] of sources) {
  const importPattern =
    /import\s+(?:([A-Za-z0-9_$]+)\s*,\s*)?(?:\{([^}]*)\}|\*\s+as\s+[A-Za-z0-9_$]+)?\s*from\s*["'](\.[^"']+)["']/g;
  for (const match of source.matchAll(importPattern)) {
    const named = match[2];
    const spec = match[3];
    const target = spec.replace("./", "");

    if (!sources.has(target)) {
      console.log(`MISSING MODULE: ${file} imports ${spec}`);
      problems++;
      continue;
    }
    if (!named) continue;

    const available = exportsOf(sources.get(target));
    for (const raw of named.split(",")) {
      const name = raw.trim().split(/\s+as\s+/)[0].trim();
      if (!name) continue;
      checked++;
      if (!available.has(name)) {
        console.log(`MISSING EXPORT: ${file} imports { ${name} } from ${spec}`);
        problems++;
      }
    }
  }
}

console.log(`checked ${checked} named imports across ${files.length} modules`);
console.log(problems === 0 ? "ESM import/export graph OK" : `${problems} problem(s) found`);
process.exit(problems === 0 ? 0 : 1);
