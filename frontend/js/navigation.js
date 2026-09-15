import { AppState } from "./state.js";
import { loadHistory } from "./history.js";

export function initNavigation() {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => {
      switchPanel(item.dataset.panel);
    });
  });
}
export function switchPanel(panelId) {
  document.querySelectorAll(".nav-item").forEach((nav) => {
    nav.classList.toggle("active", nav.dataset.panel === panelId);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.remove("active");
  });
  document.getElementById(`panel-${panelId}`).classList.add("active");
  AppState.currentPanel = panelId;
  if (panelId === "history") {
    loadHistory(1);
  }
}
export function initModeCards() {
  document.querySelectorAll("[data-mode]").forEach((card) => {
    card.addEventListener("click", () => {
      document
        .querySelectorAll("[data-mode]")
        .forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      AppState.currentMode = card.dataset.mode;
    });
  });
  document.querySelectorAll("[data-single-mode]").forEach((card) => {
    card.addEventListener("click", () => {
      document
        .querySelectorAll("[data-single-mode]")
        .forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      AppState.currentSingleMode = card.dataset.singleMode;
    });
  });
  document.querySelectorAll("[data-ao3-mode]").forEach((card) => {
    card.addEventListener("click", () => {
      document
        .querySelectorAll("[data-ao3-mode]")
        .forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      AppState.currentAo3Mode = card.dataset.ao3Mode;
    });
  });
}
