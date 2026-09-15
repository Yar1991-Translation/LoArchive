import { mi } from "./icons.js";
import { showNotification } from "./ui.js";

/* 新手引导 */
let onboardingStep = 1;
const totalSteps = 3;
export function initOnboarding() {
  if (localStorage.getItem("loarchive_onboarding_done") === "true") {
    return;
  }
  const overlay = document.getElementById("onboarding");
  const nextBtn = document.getElementById("onboarding-next");
  const skipBtn = document.getElementById("onboarding-skip");
  const dots = document.querySelectorAll(".onboarding-dot");
  setTimeout(() => {
    overlay.classList.add("show");
  }, 300);
  nextBtn.addEventListener("click", () => {
    if (onboardingStep < totalSteps) {
      onboardingStep++;
      updateOnboardingStep();
    } else {
      finishOnboarding();
    }
  });
  skipBtn.addEventListener("click", finishOnboarding);
  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      onboardingStep = parseInt(dot.dataset.step);
      updateOnboardingStep();
    });
  });
}
function updateOnboardingStep() {
  document
    .querySelectorAll(".onboarding-steps")
    .forEach((s) => s.classList.remove("active"));
  document
    .querySelector(`.onboarding-steps[data-step="${onboardingStep}"]`)
    .classList.add("active");
  document.querySelectorAll(".onboarding-dot").forEach((d) => {
    d.classList.toggle("active", parseInt(d.dataset.step) === onboardingStep);
  });
  const nextBtn = document.getElementById("onboarding-next");
  if (onboardingStep === totalSteps) {
    nextBtn.textContent = mi("rocket_launch") + " 开始使用";
  } else {
    nextBtn.textContent = "下一步 →";
  }
}
function finishOnboarding() {
  const overlay = document.getElementById("onboarding");
  overlay.classList.remove("show");
  localStorage.setItem("loarchive_onboarding_done", "true");
  createConfetti();
  showNotification("欢迎使用！如需查看帮助，请前往「设置」页面", "success");
}
function createConfetti() {
  const colors = ["#00bcd4", "#26c6da", "#ff6b9d", "#ffd700", "#00897b"];
  for (let i = 0; i < 50; i++) {
    const confetti = document.createElement("div");
    confetti.className = "confetti";
    confetti.style.cssText = `position:fixed;width:10px;height:10px;background:${colors[Math.floor(Math.random() * colors.length)]};left:${Math.random() * 100}vw;top:-20px;border-radius:${Math.random() > 0.5 ? "50%" : "2px"};z-index:20001;pointer-events:none`;
    document.body.appendChild(confetti);
    const duration = 2000 + Math.random() * 2000;
    const rotation = Math.random() * 720 - 360;
    confetti.animate(
      [
        { transform: "translateY(0) rotate(0deg)", opacity: 1 },
        { transform: `translateY(100vh) rotate(${rotation}deg)`, opacity: 0 },
      ],
      { duration, easing: "cubic-bezier(.25,.46,.45,.94)" },
    );
    setTimeout(() => confetti.remove(), duration);
  }
}
