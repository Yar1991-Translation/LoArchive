import { mi } from "./icons.js";

export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
export function showNotification(message, type = "info", duration = 4000) {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast timer";
  const icons = {
    info: mi("info"),
    success: mi("check_circle"),
    error: mi("error"),
    warning: mi("warning"),
  };
  toast.innerHTML = `<span class="toast-icon">${icons[type] || mi("info")}</span><div class="toast-body"><div class="toast-text">${escapeHtml(message)}</div></div><button class="toast-close" onclick="this.parentElement.remove()"><span class="mi" style="font-size:18px">close</span></button><div class="toast-bar" style="width:100%"></div>`;
  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });
  const bar = toast.querySelector(".toast-bar");
  if (bar) {
    bar.style.transitionDuration = duration + "ms";
    requestAnimationFrame(() => {
      bar.style.width = "0%";
    });
  }
  setTimeout(() => {
    toast.classList.remove("show");
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 400);
  }, duration);
}
let contextMenu = null;
export function initContextMenu() {
  contextMenu = document.createElement("div");
  contextMenu.className = "context-menu";
  contextMenu.innerHTML = `<div class="context-menu-item" data-action="copy"><span class="context-menu-item-icon"><span class="mi">content_copy</span></span><span class="context-menu-item-text">复制</span><span class="context-menu-item-shortcut">Ctrl+C</span></div><div class="context-menu-item" data-action="paste"><span class="context-menu-item-icon"><span class="mi">content_paste</span></span><span class="context-menu-item-text">粘贴</span><span class="context-menu-item-shortcut">Ctrl+V</span></div><div class="context-menu-item" data-action="cut"><span class="context-menu-item-icon"><span class="mi">content_cut</span></span><span class="context-menu-item-text">剪切</span><span class="context-menu-item-shortcut">Ctrl+X</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="selectall"><span class="context-menu-item-icon"><span class="mi">select_all</span></span><span class="context-menu-item-text">全选</span><span class="context-menu-item-shortcut">Ctrl+A</span></div><div class="context-menu-divider"></div><div class="context-menu-item" data-action="refresh"><span class="context-menu-item-icon"><span class="mi">refresh</span></span><span class="context-menu-item-text">刷新页面</span><span class="context-menu-item-shortcut">F5</span></div>`;
  document.body.appendChild(contextMenu);
  document.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    showContextMenu(e.clientX, e.clientY, e.target);
  });
  document.addEventListener("click", () => hideContextMenu());
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideContextMenu();
  });
  contextMenu.querySelectorAll(".context-menu-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      executeContextAction(item.dataset.action);
      hideContextMenu();
    });
  });
}
function showContextMenu(x, y, target) {
  updateContextMenuItems(target);
  contextMenu.classList.add("show");
  const menuRect = contextMenu.getBoundingClientRect();
  let posX = x,
    posY = y;
  if (x + menuRect.width > window.innerWidth)
    posX = window.innerWidth - menuRect.width - 10;
  if (y + menuRect.height > window.innerHeight)
    posY = window.innerHeight - menuRect.height - 10;
  contextMenu.style.left = posX + "px";
  contextMenu.style.top = posY + "px";
}
function hideContextMenu() {
  if (contextMenu) contextMenu.classList.remove("show");
}
function updateContextMenuItems(target) {
  const hasSelection = window.getSelection().toString().length > 0;
  const isEditable =
    target.tagName === "INPUT" ||
    target.tagName === "TEXTAREA" ||
    target.isContentEditable;
  const copyItem = contextMenu.querySelector('[data-action="copy"]');
  if (copyItem) copyItem.classList.toggle("disabled", !hasSelection);
  const cutItem = contextMenu.querySelector('[data-action="cut"]');
  if (cutItem)
    cutItem.classList.toggle("disabled", !hasSelection || !isEditable);
  const pasteItem = contextMenu.querySelector('[data-action="paste"]');
  if (pasteItem) pasteItem.classList.toggle("disabled", !isEditable);
}
async function executeContextAction(action) {
  switch (action) {
    case "copy":
      try {
        const selection = window.getSelection().toString();
        if (selection) {
          await navigator.clipboard.writeText(selection);
          showNotification("已复制到剪贴板", "success");
        }
      } catch (e) {
        document.execCommand("copy");
      }
      break;
    case "paste":
      try {
        const text = await navigator.clipboard.readText();
        const activeEl = document.activeElement;
        if (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA") {
          const start = activeEl.selectionStart;
          const end = activeEl.selectionEnd;
          activeEl.value =
            activeEl.value.slice(0, start) + text + activeEl.value.slice(end);
          activeEl.selectionStart = activeEl.selectionEnd = start + text.length;
        }
      } catch (e) {
        document.execCommand("paste");
      }
      break;
    case "cut":
      try {
        const selection = window.getSelection().toString();
        if (selection) {
          await navigator.clipboard.writeText(selection);
          document.execCommand("delete");
          showNotification("已剪切到剪贴板", "success");
        }
      } catch (e) {
        document.execCommand("cut");
      }
      break;
    case "selectall":
      const activeEl = document.activeElement;
      if (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA") {
        activeEl.select();
      } else {
        document.execCommand("selectAll");
      }
      break;
    case "refresh":
      window.location.reload();
      break;
  }
}
let tooltipEl = null;
export function initTooltips() {
  tooltipEl = document.createElement("div");
  tooltipEl.className = "tooltip";
  document.body.appendChild(tooltipEl);
  document.querySelectorAll("[title]").forEach((el) => {
    const title = el.getAttribute("title");
    el.removeAttribute("title");
    el.dataset.tooltip = title;
    el.addEventListener("mouseenter", showTooltip);
    el.addEventListener("mouseleave", hideTooltip);
    el.addEventListener("mousemove", moveTooltip);
  });
}
function showTooltip(e) {
  const text = e.target.dataset.tooltip;
  if (!text) return;
  tooltipEl.textContent = text;
  tooltipEl.classList.add("show", "top");
  positionTooltip(e);
}
function hideTooltip() {
  tooltipEl.classList.remove("show");
}
function moveTooltip(e) {
  positionTooltip(e);
}
function positionTooltip(e) {
  const x = e.clientX;
  const y = e.clientY;
  const rect = tooltipEl.getBoundingClientRect();
  let posX = x - rect.width / 2;
  let posY = y - rect.height - 12;
  if (posX < 10) posX = 10;
  if (posX + rect.width > window.innerWidth - 10)
    posX = window.innerWidth - rect.width - 10;
  if (posY < 10) {
    posY = y + 20;
    tooltipEl.classList.remove("top");
    tooltipEl.classList.add("bottom");
  }
  tooltipEl.style.left = posX + "px";
  tooltipEl.style.top = posY + "px";
}
