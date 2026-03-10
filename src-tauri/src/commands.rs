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
