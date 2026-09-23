/** 设计令牌与三套主题（浅色 / 深色 / 黑白）。
 *
 * 所有主题都从同一组令牌键派生：tokens 定义值 → applyTheme 写入 CSS 变量
 * 并生成 Naive UI 的主题覆盖，保证 Web 组件与 Naive UI 组件永远同源。
 */

export type ThemeName = "light" | "dark" | "bw";

export interface ThemeTokens {
  /** 应用最底层背景 */
  bg: string;
  /** 卡片 / 面板表面色 */
  surface: string;
  /** 次级表面（输入框、代码块等） */
  surfaceAlt: string;
  /** 悬停态表面 */
  surfaceHover: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  border: string;
  borderStrong: string;
  primary: string;
  primaryHover: string;
  primaryPressed: string;
  primaryText: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  radius: string;
  radiusSmall: string;
  shadow: string;
  /** 任务坞 / 顶栏等强调表面 */
  chrome: string;
  /** 进度条轨道 */
  track: string;
}

const light: ThemeTokens = {
  bg: "#f4f5f9",
  surface: "#ffffff",
  surfaceAlt: "#f0f1f6",
  surfaceHover: "#e9ebf3",
  text: "#1c1e27",
  textSecondary: "#4a4d5c",
  textMuted: "#8a8da0",
  border: "#e3e5ee",
  borderStrong: "#c9ccdd",
  primary: "#5a5fd6",
  primaryHover: "#6d72e0",
  primaryPressed: "#4a4fc2",
  primaryText: "#ffffff",
  success: "#2e9e63",
  warning: "#d08a1f",
  error: "#d24b4b",
  info: "#3a7ec2",
  radius: "12px",
  radiusSmall: "8px",
  shadow: "0 1px 3px rgba(23, 25, 40, 0.06), 0 8px 24px rgba(23, 25, 40, 0.07)",
  chrome: "#ffffff",
  track: "#e8e9f1",
};

const dark: ThemeTokens = {
  bg: "#111218",
  surface: "#191a22",
  surfaceAlt: "#22232e",
  surfaceHover: "#2a2b38",
  text: "#e8e9f0",
  textSecondary: "#b4b6c6",
  textMuted: "#767a90",
  border: "#2a2b38",
  borderStrong: "#3d3f52",
  primary: "#7d82ec",
  primaryHover: "#8f94f1",
  primaryPressed: "#6b70dd",
  primaryText: "#0f1015",
  success: "#4cc08a",
  warning: "#e3a94e",
  error: "#ef7070",
  info: "#63a4e8",
  radius: "12px",
  radiusSmall: "8px",
  shadow: "0 1px 3px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.45)",
  chrome: "#191a22",
  track: "#262733",
};

const bw: ThemeTokens = {
  bg: "#ffffff",
  surface: "#ffffff",
  surfaceAlt: "#f2f2f2",
  surfaceHover: "#e6e6e6",
  text: "#000000",
  textSecondary: "#1a1a1a",
  textMuted: "#555555",
  border: "#000000",
  borderStrong: "#000000",
  primary: "#000000",
  primaryHover: "#1f1f1f",
  primaryPressed: "#000000",
  primaryText: "#ffffff",
  success: "#000000",
  warning: "#000000",
  error: "#000000",
  info: "#000000",
  radius: "0px",
  radiusSmall: "0px",
  shadow: "4px 4px 0 #000000",
  chrome: "#ffffff",
  track: "#f2f2f2",
};

export const THEMES: Record<ThemeName, ThemeTokens> = { light, dark, bw };

export const THEME_LABELS: Record<ThemeName, string> = {
  light: "默认",
  dark: "深色",
  bw: "黑白块",
};

export interface TokenVariableMapping {
  [cssVar: string]: keyof ThemeTokens;
}

/** CSS 变量名 → 令牌键 的映射（--la-* 前缀） */
export const CSS_VAR_MAPPING: TokenVariableMapping = {
  "--la-bg": "bg",
  "--la-surface": "surface",
  "--la-surface-alt": "surfaceAlt",
  "--la-surface-hover": "surfaceHover",
  "--la-text": "text",
  "--la-text-secondary": "textSecondary",
  "--la-text-muted": "textMuted",
  "--la-border": "border",
  "--la-border-strong": "borderStrong",
  "--la-primary": "primary",
  "--la-primary-hover": "primaryHover",
  "--la-primary-pressed": "primaryPressed",
  "--la-primary-text": "primaryText",
  "--la-success": "success",
  "--la-warning": "warning",
  "--la-error": "error",
  "--la-info": "info",
  "--la-radius": "radius",
  "--la-radius-small": "radiusSmall",
  "--la-shadow": "shadow",
  "--la-chrome": "chrome",
  "--la-track": "track",
};

/** 由令牌生成 Naive UI 深色判定与主题覆盖 */
export function buildNaiveOverrides(tokens: ThemeTokens) {
  const isDark = tokens === dark;
  return {
    darkTheme: isDark,
    overrides: {
      common: {
        fontFamily:
          "'Noto Sans SC', -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif",
        borderRadius: tokens.radius,
        borderRadiusSmall: tokens.radiusSmall,
        primaryColor: tokens.primary,
        primaryColorHover: tokens.primaryHover,
        primaryColorPressed: tokens.primaryPressed,
        primaryColorSuppl: tokens.primaryHover,
        errorColor: tokens.error,
        errorColorHover: tokens.error,
        errorColorPressed: tokens.error,
        warningColor: tokens.warning,
        warningColorHover: tokens.warning,
        warningColorPressed: tokens.warning,
        successColor: tokens.success,
        successColorHover: tokens.success,
        successColorPressed: tokens.success,
        infoColor: tokens.info,
        infoColorHover: tokens.info,
        infoColorPressed: tokens.info,
        bodyColor: tokens.bg,
        cardColor: tokens.surface,
        modalColor: tokens.surface,
        popoverColor: tokens.surface,
        inputColor: tokens.surfaceAlt,
        actionColor: tokens.surfaceAlt,
        hoverColor: tokens.surfaceHover,
        borderColor: tokens.border,
        dividerColor: tokens.border,
        textColorBase: tokens.text,
        textColor1: tokens.text,
        textColor2: tokens.textSecondary,
        textColor3: tokens.textMuted,
        placeholderColor: tokens.textMuted,
      },
      Card: {
        borderRadius: tokens.radius,
        borderColor: tokens.border,
        // 黑白块主题用粗描边区分卡片
        border: `1px solid ${tokens.border}`,
        boxShadow: tokens.shadow,
      },
      Button: {
        borderRadius: tokens.radiusSmall,
        fontWeight: "500",
      },
      Progress: {
        fillColor: tokens.primary,
        railColor: tokens.track,
      },
    },
  };
}
