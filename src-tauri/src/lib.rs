use tauri::Manager;
use std::process::{Command, Child, Stdio};
use std::sync::Mutex;

// 全局存储后端进程
static BACKEND_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

fn start_backend() -> Result<Child, std::io::Error> {
    // 获取当前可执行文件的目录
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| std::env::current_dir().unwrap());
    
    // 尝试多个可能的路径找到 web_app.py
    let possible_paths = vec![
        exe_dir.join("web_app.py"),
        exe_dir.join("../web_app.py"),
        exe_dir.join("../../web_app.py"),
        exe_dir.join("../../../web_app.py"),
        std::env::current_dir().unwrap().join("web_app.py"),
    ];
    
    let web_app_path = possible_paths
        .iter()
        .find(|p| p.exists())
        .cloned()
        .unwrap_or_else(|| exe_dir.join("web_app.py"));
    
    let working_dir = web_app_path.parent().unwrap_or(&exe_dir);
    
    println!("Starting backend from: {:?}", web_app_path);
    println!("Working directory: {:?}", working_dir);
    
    // 在 Windows 上使用 pythonw 避免显示控制台窗口，如果失败则使用 python
    #[cfg(target_os = "windows")]
    {
        Command::new("pythonw")
            .arg(&web_app_path)
            .current_dir(working_dir)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .or_else(|_| {
                Command::new("python")
                    .arg(&web_app_path)
                    .current_dir(working_dir)
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
            })
    }
    
    #[cfg(not(target_os = "windows"))]
    {
        Command::new("python3")
            .arg(&web_app_path)
            .current_dir(working_dir)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .or_else(|_| {
                Command::new("python")
                    .arg(&web_app_path)
                    .current_dir(working_dir)
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
            })
    }
}

fn stop_backend() {
    if let Ok(mut guard) = BACKEND_PROCESS.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
            println!("Backend process stopped");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 启动后端服务
            match start_backend() {
                Ok(child) => {
                    println!("Backend started with PID: {}", child.id());
                    if let Ok(mut guard) = BACKEND_PROCESS.lock() {
                        *guard = Some(child);
                    }
                    // 等待后端启动
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }
                Err(e) => {
                    eprintln!("Failed to start backend: {}", e);
                }
            }
            
            // 日志插件 (仅开发模式)
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            
            // 获取主窗口并设置标题
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("LoArchive");
            }
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if window.label() == "main" {
                    // 关闭窗口时停止后端
                    stop_backend();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
