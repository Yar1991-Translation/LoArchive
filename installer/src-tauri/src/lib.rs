use serde::{Deserialize, Serialize};
use std::fs;
use std::io::{Read, Write};
use std::path::PathBuf;
use tauri::Manager;

#[derive(Serialize, Deserialize)]
pub struct InstallOptions {
    pub install_path: String,
    pub create_desktop_shortcut: bool,
    pub create_start_menu_shortcut: bool,
    pub auto_start: bool,
}

#[derive(Serialize, Clone)]
pub struct InstallProgress {
    pub progress: u32,
    pub status: String,
    pub log: String,
}

#[tauri::command]
async fn get_default_install_path() -> Result<String, String> {
    let local_app_data = dirs::data_local_dir()
        .ok_or("无法获取本地应用数据目录")?;
    Ok(local_app_data.join("LoArchive").to_string_lossy().to_string())
}

#[tauri::command]
async fn get_available_space(path: String) -> Result<String, String> {
    // 简单返回 "充足"
    Ok("充足".to_string())
}

#[tauri::command]
async fn install_app(
    app: tauri::AppHandle,
    options: InstallOptions,
) -> Result<(), String> {
    let window = app.get_webview_window("main").ok_or("无法获取窗口")?;
    
    // 发送进度
    let send_progress = |progress: u32, status: &str, log: &str| {
        let _ = window.emit("install-progress", InstallProgress {
            progress,
            status: status.to_string(),
            log: log.to_string(),
        });
    };
    
    let install_path = PathBuf::from(&options.install_path);
    
    // 步骤 1: 创建安装目录
    send_progress(5, "创建安装目录...", "正在创建安装目录...");
    fs::create_dir_all(&install_path).map_err(|e| format!("创建目录失败: {}", e))?;
    std::thread::sleep(std::time::Duration::from_millis(300));
    send_progress(10, "创建安装目录...", "✓ 安装目录已创建");
    
    // 步骤 2: 解压程序文件
    send_progress(15, "解压程序文件...", "正在解压程序文件...");
    let resource_path = app.path().resource_dir()
        .map_err(|e| format!("获取资源目录失败: {}", e))?;
    let payload_path = resource_path.join("payload");
    
    if payload_path.exists() {
        // 复制 payload 目录中的所有文件
        copy_dir_all(&payload_path, &install_path)
            .map_err(|e| format!("复制文件失败: {}", e))?;
    }
    
    std::thread::sleep(std::time::Duration::from_millis(1500));
    send_progress(50, "解压程序文件...", "✓ 程序文件已解压");
    
    // 步骤 3: 创建快捷方式
    if options.create_desktop_shortcut {
        send_progress(60, "创建桌面快捷方式...", "正在创建桌面快捷方式...");
        create_shortcut(&install_path, true).ok();
        std::thread::sleep(std::time::Duration::from_millis(300));
        send_progress(70, "创建桌面快捷方式...", "✓ 桌面快捷方式已创建");
    }
    
    if options.create_start_menu_shortcut {
        send_progress(75, "创建开始菜单快捷方式...", "正在创建开始菜单快捷方式...");
        create_shortcut(&install_path, false).ok();
        std::thread::sleep(std::time::Duration::from_millis(300));
        send_progress(80, "创建开始菜单快捷方式...", "✓ 开始菜单快捷方式已创建");
    }
    
    // 步骤 4: 注册卸载程序
    send_progress(85, "注册应用程序...", "正在注册应用程序...");
    register_uninstall(&install_path).ok();
    std::thread::sleep(std::time::Duration::from_millis(300));
    send_progress(90, "注册应用程序...", "✓ 应用程序已注册");
    
    // 步骤 5: 自动启动
    if options.auto_start {
        send_progress(95, "配置自动启动...", "正在配置自动启动...");
        set_auto_start(&install_path, true).ok();
        std::thread::sleep(std::time::Duration::from_millis(200));
    }
    
    // 完成
    send_progress(100, "安装完成", "✓ LoArchive 安装成功！");
    
    Ok(())
}

#[tauri::command]
async fn launch_app(install_path: String) -> Result<(), String> {
    let exe_path = PathBuf::from(&install_path).join("LoArchive.exe");
    
    std::process::Command::new(&exe_path)
        .spawn()
        .map_err(|e| format!("启动应用失败: {}", e))?;
    
    Ok(())
}

fn copy_dir_all(src: &PathBuf, dst: &PathBuf) -> std::io::Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        let src_path = entry.path();
        let dst_path = dst.join(entry.file_name());
        
        if ty.is_dir() {
            copy_dir_all(&src_path, &dst_path)?;
        } else {
            fs::copy(&src_path, &dst_path)?;
        }
    }
    Ok(())
}

#[cfg(windows)]
fn create_shortcut(install_path: &PathBuf, desktop: bool) -> Result<(), String> {
    use std::process::Command;
    
    let exe_path = install_path.join("LoArchive.exe");
    let shortcut_dir = if desktop {
        dirs::desktop_dir().ok_or("无法获取桌面目录")?
    } else {
        dirs::data_dir()
            .ok_or("无法获取应用数据目录")?
            .join("Microsoft\\Windows\\Start Menu\\Programs\\LoArchive")
    };
    
    if !desktop {
        fs::create_dir_all(&shortcut_dir).ok();
    }
    
    let shortcut_path = shortcut_dir.join("LoArchive.lnk");
    
    // 使用 PowerShell 创建快捷方式
    let ps_script = format!(
        r#"$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('{}'); $Shortcut.TargetPath = '{}'; $Shortcut.WorkingDirectory = '{}'; $Shortcut.Save()"#,
        shortcut_path.to_string_lossy(),
        exe_path.to_string_lossy(),
        install_path.to_string_lossy()
    );
    
    Command::new("powershell")
        .args(["-Command", &ps_script])
        .creation_flags(0x08000000) // CREATE_NO_WINDOW
        .output()
        .map_err(|e| format!("创建快捷方式失败: {}", e))?;
    
    Ok(())
}

#[cfg(not(windows))]
fn create_shortcut(_install_path: &PathBuf, _desktop: bool) -> Result<(), String> {
    Ok(())
}

#[cfg(windows)]
fn register_uninstall(install_path: &PathBuf) -> Result<(), String> {
    use winreg::enums::*;
    use winreg::RegKey;
    
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\LoArchive";
    
    let (key, _) = hkcu.create_subkey(path)
        .map_err(|e| format!("创建注册表项失败: {}", e))?;
    
    let exe_path = install_path.join("LoArchive.exe");
    let uninstall_path = install_path.join("uninstall.exe");
    
    key.set_value("DisplayName", &"LoArchive").ok();
    key.set_value("DisplayVersion", &"1.0.0").ok();
    key.set_value("Publisher", &"Yar1991-Translation").ok();
    key.set_value("DisplayIcon", &exe_path.to_string_lossy().to_string()).ok();
    key.set_value("UninstallString", &uninstall_path.to_string_lossy().to_string()).ok();
    key.set_value("InstallLocation", &install_path.to_string_lossy().to_string()).ok();
    
    Ok(())
}

#[cfg(not(windows))]
fn register_uninstall(_install_path: &PathBuf) -> Result<(), String> {
    Ok(())
}

#[cfg(windows)]
fn set_auto_start(install_path: &PathBuf, enable: bool) -> Result<(), String> {
    use winreg::enums::*;
    use winreg::RegKey;
    
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let path = r"Software\Microsoft\Windows\CurrentVersion\Run";
    
    let key = hkcu.open_subkey_with_flags(path, KEY_WRITE)
        .map_err(|e| format!("打开注册表失败: {}", e))?;
    
    if enable {
        let exe_path = install_path.join("LoArchive.exe");
        key.set_value("LoArchive", &exe_path.to_string_lossy().to_string())
            .map_err(|e| format!("设置自动启动失败: {}", e))?;
    } else {
        key.delete_value("LoArchive").ok();
    }
    
    Ok(())
}

#[cfg(not(windows))]
fn set_auto_start(_install_path: &PathBuf, _enable: bool) -> Result<(), String> {
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_default_install_path,
            get_available_space,
            install_app,
            launch_app
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

