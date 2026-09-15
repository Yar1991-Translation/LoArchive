import { API_BASE } from "./api.js";
import { mi } from "./icons.js";
import { escapeHtml, showNotification } from "./ui.js";

/* 下载历史功能 */
let historyPage = 1;

export async function loadHistory(page) {
  if (page === undefined) page = historyPage;
  historyPage = page;

  const search = document.getElementById("historySearch").value.trim();
  const filter = document.getElementById("historyFilter").value;
  const source = document.getElementById("historySource").value;
  const loading = document.getElementById("historyLoading");
  const list = document.getElementById("historyList");

  loading.style.display = "block";
  list.style.display = "none";

  try {
    const params = new URLSearchParams({ page, search, type: filter, source });
    const res = await fetch(`${API_BASE}/api/history?${params}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    loading.style.display = "none";
    list.style.display = "block";

    renderHistoryList(data.items, data.total);
    renderHistoryStats(data.stats, data.page, data.per_page, data.total);
    renderPagination(data.page, data.total_pages);
  } catch (e) {
    loading.style.display = "none";
    list.style.display = "block";
    list.innerHTML =
      '<div style="text-align:center;padding:40px;color:var(--md3-error);">加载失败: ' +
      escapeHtml(e.message) +
      "</div>";
  }
}

function renderHistoryList(items, total) {
  const container = document.getElementById("historyList");
  if (!items.length) {
    container.innerHTML =
      '<div style="text-align:center;padding:40px;color:var(--text-muted);">' +
      (total === 0
        ? '<span class="mi">mark_email_read</span> 暂无下载记录'
        : '<span class="mi">search</span> 没有匹配的记录') +
      "</div>";
    return;
  }
  container.innerHTML = items
    .map((item) => {
      const icon =
        item.type === "image"
          ? mi("image")
          : item.type === "ao3"
            ? mi("auto_stories")
            : mi("edit_note");
      const source = item.source === "ao3" ? "AO3" : "Lofter";
      const filePath = item.file_path ? escapeHtml(item.file_path) : "";
      return `<div class="history-item">
            <span class="history-icon">${icon}</span>
            <div class="history-info">
                <div class="history-title">${escapeHtml(item.title || "未知标题")}</div>
                <div class="history-meta">
                    <span><span class="mi">person</span> ${escapeHtml(item.author || "未知作者")}</span>
                    <span><span class="mi">folder</span> ${source}</span>
                    <span><span class="mi">schedule</span> ${item.download_time || ""}</span>
                </div>
                ${filePath ? `<div class="history-meta"><span><span class="mi">folder_open</span> ${filePath}</span></div>` : ""}
            </div>
            <div class="history-actions">
                <button class="history-btn open" onclick="copyFilePath('${escapeHtml(item.file_path || "")}')">复制路径</button>
                <button class="history-btn delete" onclick="deleteHistoryItem('${item.id}')">删除</button>
            </div>
        </div>`;
    })
    .join("");
}

function renderHistoryStats(stats, page, perPage, total) {
  const el = document.getElementById("historyStats");
  if (!el) return;
  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);
  el.innerHTML =
    total > 0
      ? mi("bar_chart") +
        " 共 <strong>" +
        stats.total +
        "</strong> 条（" +
        start +
        "-" +
        end +
        "）| " +
        mi("add_photo_alternate") +
        " 图片 <strong>" +
        stats.images +
        "</strong> | " +
        mi("edit_note") +
        " 文章 <strong>" +
        stats.articles +
        "</strong>"
      : mi("bar_chart") + " 暂无记录";
}

function renderPagination(current, total) {
  const container = document.getElementById("historyPagination");
  if (total <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `<button class="page-btn" onclick="loadHistory(1)" ${current <= 1 ? "disabled" : ""}>首页</button>`;
  html += `<button class="page-btn" onclick="loadHistory(${current - 1})" ${current <= 1 ? "disabled" : ""}>‹</button>`;

  // 显示当前页附近的页码
  let startP = Math.max(1, current - 2);
  let endP = Math.min(total, current + 2);
  if (startP > 1)
    html += '<span style="padding:0 6px;color:var(--text-muted);">…</span>';
  for (let i = startP; i <= endP; i++) {
    html += `<button class="page-btn ${i === current ? "active" : ""}" onclick="loadHistory(${i})">${i}</button>`;
  }
  if (endP < total)
    html += '<span style="padding:0 6px;color:var(--text-muted);">…</span>';

  html += `<button class="page-btn" onclick="loadHistory(${current + 1})" ${current >= total ? "disabled" : ""}>›</button>`;
  html += `<button class="page-btn" onclick="loadHistory(${total})" ${current >= total ? "disabled" : ""}>末页</button>`;
  html += `<span style="margin-left:8px;font-size:12px;color:var(--text-muted);">共${total}页</span>`;
  container.innerHTML = html;
}

export function copyFilePath(path) {
  if (!path) return showNotification("无文件路径", "warning");
  navigator.clipboard.writeText(path).then(
    () => showNotification("路径已复制", "success"),
    () => showNotification("复制失败", "error"),
  );
}

export async function deleteHistoryItem(id) {
  if (!confirm("确定删除这条记录吗？")) return;
  try {
    const res = await fetch(`${API_BASE}/api/history/delete/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    showNotification("已删除", "success");
    loadHistory(historyPage);
  } catch (e) {
    showNotification("删除失败: " + e.message, "error");
  }
}

export async function clearHistory() {
  if (!confirm("确定清空所有下载历史吗？此操作不可恢复！")) return;
  try {
    const res = await fetch(`${API_BASE}/api/history/clear`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    showNotification("历史已清空", "success");
    loadHistory(1);
  } catch (e) {
    showNotification("清空失败: " + e.message, "error");
  }
}
