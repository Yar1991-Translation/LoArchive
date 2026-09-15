export function initTauri() {
  const isTauri =
    window.__TAURI__ !== undefined ||
    window.__TAURI_INTERNALS__ !== undefined ||
    navigator.userAgent.includes("Tauri");
  if (!isTauri) {
    const titlebar = document.getElementById("titlebar");
    if (titlebar) titlebar.style.display = "none";
    const container = document.querySelector(".app-container");
    if (container) container.style.paddingTop = "0";
    return;
  }
  console.log("LoArchive: Tauri 环境已检测");
  const setupWindowControls = async () => {
    try {
      let appWindow;
      if (window.__TAURI__ && window.__TAURI__.window) {
        const { getCurrentWindow } = window.__TAURI__.window;
        appWindow = getCurrentWindow();
      } else {
        const { getCurrentWindow } = await import("@tauri-apps/api/window");
        appWindow = getCurrentWindow();
      }
      if (!appWindow) {
        console.error("无法获取 Tauri 窗口实例");
        return;
      }
      const btnMinimize = document.getElementById("btn-minimize");
      const btnMaximize = document.getElementById("btn-maximize");
      const btnClose = document.getElementById("btn-close");
      if (btnMinimize) btnMinimize.onclick = () => appWindow.minimize();
      if (btnMaximize)
        btnMaximize.onclick = async () => {
          (await appWindow.isMaximized())
            ? appWindow.unmaximize()
            : appWindow.maximize();
        };
      if (btnClose) btnClose.onclick = () => appWindow.close();
      const titlebarLeft = document.querySelector(".titlebar-left");
      if (titlebarLeft) {
        titlebarLeft.addEventListener("dblclick", async () => {
          (await appWindow.isMaximized())
            ? appWindow.unmaximize()
            : appWindow.maximize();
        });
      }
      console.log("窗口控制按钮已绑定");
    } catch (e) {
      console.error("Tauri 窗口控制初始化失败:", e);
    }
  };
  if (document.readyState === "complete") {
    setupWindowControls();
  } else {
    window.addEventListener("load", setupWindowControls);
  }
}
