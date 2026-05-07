use crate::config::AppConfig;
use crate::device::DeviceManager;
use crate::models::*;
use tauri::State;
use tokio::sync::Mutex;

type AppState = Mutex<DeviceManager>;

#[tauri::command]
pub async fn list_devices(state: State<'_, AppState>) -> Result<Vec<DeviceInfo>, String> {
    let mut mgr = state.lock().await;
    Ok(mgr.scan_devices().await)
}

#[tauri::command]
pub async fn send_command(
    state: State<'_, AppState>,
    cmd_type: String,
    x: f32,
    y: f32,
    end_x: f32,
    end_y: f32,
    duration_ms: i32,
    text: Option<String>,
    key_code: i32,
    target_devices: Vec<String>,
    tap_view_id: Option<String>,
    tap_text: Option<String>,
    tap_content_desc: Option<String>,
) -> Result<CommandResult, String> {
    let mut mgr = state.lock().await;
    Ok(mgr
        .send_command(
            cmd_type,
            x,
            y,
            end_x,
            end_y,
            duration_ms,
            text,
            key_code,
            target_devices,
            tap_view_id,
            tap_text,
            tap_content_desc,
        )
        .await)
}

#[tauri::command]
pub async fn get_screenshot(
    state: State<'_, AppState>,
    serial: String,
) -> Result<ScreenshotResult, String> {
    let mut mgr = state.lock().await;
    mgr.get_screenshot(&serial).await
}

#[tauri::command]
pub async fn start_mirror(state: State<'_, AppState>, serial: String) -> Result<(), String> {
    let mut mgr = state.lock().await;
    mgr.start_mirror(&serial).await
}

#[tauri::command]
pub async fn stop_mirror(state: State<'_, AppState>, serial: String) -> Result<(), String> {
    let mut mgr = state.lock().await;
    mgr.stop_mirror(&serial).await
}

#[tauri::command]
pub async fn install_agent(
    state: State<'_, AppState>,
    serial: String,
) -> Result<InstallResult, String> {
    let mgr = state.lock().await;
    Ok(mgr.install_agent(&serial).await)
}

#[tauri::command]
pub async fn download_apk() -> Result<DownloadApkResult, String> {
    // Загружаем конфиг ещё раз (он лёгкий), чтобы взять URL.
    let config = AppConfig::load();
    let url = match config.apk_download_url {
        Some(u) if !u.is_empty() => u,
        _ => {
            return Ok(DownloadApkResult {
                success: false,
                message: "APK download URL is not configured in config.json (apk_download_url)".into(),
                path: None,
            })
        }
    };

    // Кладём agent.apk в текущую рабочую директорию процесса.
    // Это хорошо согласуется с DRM/лоадером: он может поднять процесс
    // из своей папки и ожидать, что вспомогательные файлы будут там.
    let cwd = std::env::current_dir().map_err(|e| format!("Failed to resolve current dir: {e}"))?;
    let target_path = cwd.join("agent.apk");

    let url_clone = url.clone();
    let target_clone = target_path.clone();

    let result = tauri::async_runtime::spawn(async move {
        let client = reqwest::Client::new();
        let resp = client
            .get(&url_clone)
            .send()
            .await
            .map_err(|e| format!("Download failed: {e}"))?;

        if !resp.status().is_success() {
            return Err(format!("HTTP error: {}", resp.status()));
        }

        let bytes = resp
            .bytes()
            .await
            .map_err(|e| format!("Failed to read body: {e}"))?;

        if let Some(parent) = target_clone.parent() {
            std::fs::create_dir_all(parent).map_err(|e| format!("Failed to create dir: {e}"))?;
        }

        // Пишем во временный файл и переименовываем для атомарности.
        let tmp_path = target_clone.with_extension("apk.tmp");
        std::fs::write(&tmp_path, &bytes).map_err(|e| format!("Failed to write file: {e}"))?;
        std::fs::rename(&tmp_path, &target_clone)
            .map_err(|e| format!("Failed to move file: {e}"))?;

        Ok(())
    })
    .await
    .map_err(|e| format!("Join error: {e}"))?;

    match result {
        Ok(()) => Ok(DownloadApkResult {
            success: true,
            message: "APK downloaded successfully".into(),
            path: Some(target_path.display().to_string()),
        }),
        Err(msg) => Ok(DownloadApkResult {
            success: false,
            message: msg,
            path: None,
        }),
    }
}
