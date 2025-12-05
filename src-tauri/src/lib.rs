use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use std::sync::Mutex;

// 存储后端进程
static BACKEND_HANDLE: Mutex<Option<tauri_plugin_shell::process::CommandChild>> = Mutex::new(None);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let app_handle = app.handle().clone();
            
            // 启动后端 sidecar
            std::thread::spawn(move || {
                match start_backend_sidecar(&app_handle) {
                    Ok(_) => println!("Backend sidecar started successfully"),
                    Err(e) => eprintln!("Failed to start backend sidecar: {}", e),
                }
            });
            
            // 等待后端启动
            std::thread::sleep(std::time::Duration::from_secs(2));
            
            // 日志插件 (仅开发模式)
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            
            // 设置窗口标题
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("LoArchive");
            }
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if window.label() == "main" {
                    stop_backend();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn start_backend_sidecar(app: &tauri::AppHandle) -> Result<(), String> {
    let shell = app.shell();
    
    // sidecar 名称需要与 tauri.conf.json 中 bundle.externalBin 配置匹配
    let sidecar = shell
        .sidecar("loarchive-backend")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?;
    
    let (mut rx, child) = sidecar
        .spawn()
        .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;
    
    // 存储进程句柄
    if let Ok(mut guard) = BACKEND_HANDLE.lock() {
        *guard = Some(child);
    }
    
    // 在后台读取输出（可选，用于调试）
    std::thread::spawn(move || {
        while let Some(event) = rx.blocking_recv() {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    println!("[Backend] {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    eprintln!("[Backend Error] {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                    println!("[Backend] Process terminated with status: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
    });
    
    Ok(())
}

fn stop_backend() {
    if let Ok(mut guard) = BACKEND_HANDLE.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
            println!("Backend process stopped");
        }
    }
}
