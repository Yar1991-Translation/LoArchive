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
  bg: "#f0fdfa",
  surface: "#ffffff",
  surfaceAlt: "#e8f5f3",
  surfaceHover: "#e8f5f3",
  text: "#1a1a1a",
  textSecondary: "#424242",
  textMuted: "#757575",
  border: "#b2ebf2",
  borderStrong: "#006064",
  primary: "#00bcd4",
  primaryHover: "#26c6da",
  primaryPressed: "#00a5bb",
  primaryText: "#ffffff",
  success: "#00897b",
  warning: "#ff9800",
  error: "#b00020",
  info: "#0288d1",
  radius: "12px",
  radiusSmall: "8px",
  shadow: "0 4px 12px rgba(0, 188, 212, 0.12), 0 8px 24px rgba(0, 188, 212, 0.16)",
  chrome: "#ffffff",
  track: "#b2ebf2",
};

const dark: ThemeTokens = {
  bg: "#0f1a1b",
  surface: "#182222",
  surfaceAlt: "#243333",
  surfaceHover: "#243333",
  text: "#e0f2f1",
  textSecondary: "#a8c4c8",
  textMuted: "#6a9095",
  border: "#2d4040",
  borderStrong: "#5a8a8e",
  primary: "#4dd0e1",
  primaryHover: "#80deea",
  primaryPressed: "#35b8c9",
  primaryText: "#000000",
  success: "#4db6ac",
  warning: "#ffb74d",
  error: "#ff6b6b",
  info: "#4fc3f7",
  radius: "12px",
  radiusSmall: "8px",
  shadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
  chrome: "#182222",
  track: "#2d4040",
};

const bw: ThemeTokens = {
  bg: "#ffffff",
  surface: "#ffffff",
  surfaceAlt: "#f0f0f0",
  surfaceHover: "#f0f0f0",
  text: "#000000",
  textSecondary: "#333333",
  textMuted: "#666666",
  border: "#cccccc",
  borderStrong: "#000000",
  primary: "#000000",
  primaryHover: "#333333",
  primaryPressed: "#000000",
  primaryText: "#ffffff",
  success: "#000000",
  warning: "#333333",
  error: "#000000",
  info: "#000000",
  radius: "0px",
  radiusSmall: "0px",
  shadow: "none",
  chrome: "#ffffff",
  track: "#e0e0e0",
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
