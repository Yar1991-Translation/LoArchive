/** 后端 API 类型定义（与 loarchive/schemas.py 的 Pydantic 模型一一对应）。 */

export interface TaskStatus {
  running: boolean;
  current_task: string | null;
  progress: number;
  message: string;
  logs: string[];
  error: string | null;
}

export interface AppConfig {
  login_key: string;
  login_auth: string;
  has_auth: boolean;
  file_path: string;
}

export interface AppSettings {
  save_path: string;
  auto_dedup: boolean;
  notify_on_complete: boolean;
}

export interface HistoryItem {
  id: string;
  type: string;
  url: string;
  title: string;
  author: string;
  file_path: string;
  source: string;
  download_time: string;
  timestamp: number;
}

export interface HistoryStats {
  total: number;
  images: number;
  articles: number;
}

export interface HistoryQueryResult {
  items: HistoryItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  stats: HistoryStats;
}

export interface HistoryCheckResult {
  downloaded: boolean;
  url: string;
}

export interface FileEntry {
  name: string;
  path: string;
  size: number;
  type: "image" | "text";
}

export interface FilesResult {
  files: FileEntry[];
  total: number;
}

/** 任务类型与其参数（与 schemas.TASK_PARAM_MODELS 对应） */
export type TaskType = "like_share_tag" | "author_img" | "author_txt" | "single_img" | "single_txt" | "ao3";

export interface LstParams {
  url: string;
  mode: "like1" | "like2" | "share" | "tag";
  save_mode: { article: number; text: number; "long article": number; img: number };
  start_time: string;
  export_pdf: boolean;
}

export interface AuthorImgParams {
  author_url: string;
  start_time: string;
  end_time: string;
}

export interface AuthorTxtParams {
  author_url: string;
}

export interface Ao3Params {
  urls: string[];
  mode: "work" | "series" | "author" | "tag";
  download_chapters: boolean;
  save_metadata: boolean;
  export_pdf: boolean;
  export_epub: boolean;
  max_pages: number;
}
