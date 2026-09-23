/** 前端入口：装配 Pinia、Naive UI 通知上下文与根组件。 */

import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-sans-sc/500.css";
import "@fontsource/noto-sans-sc/700.css";
import "material-symbols/outlined.css";

import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import "./styles/global.css";
import { initDevtools } from "./devtools";

const app = createApp(App);
app.use(createPinia());
app.mount("#app");

initDevtools();
