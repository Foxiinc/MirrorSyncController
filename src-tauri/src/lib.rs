mod adb;
mod agent;
mod commands;
mod config;
mod device;
mod models;

use config::AppConfig;
use device::DeviceManager;
use tauri::Manager;
use tokio::sync::Mutex;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "mirror_sync_lib=info".into()),
        )
        .init();

    let config = AppConfig::load();
    tracing::info!("MirrorSync Controller starting");

    tauri::Builder::default()
        .setup(move |app| {
            let mgr = tauri::async_runtime::block_on(DeviceManager::new(config));
            app.manage(Mutex::new(mgr));
            tracing::info!("DeviceManager ready");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::list_devices,
            commands::send_command,
            commands::get_screenshot,
            commands::start_mirror,
            commands::stop_mirror,
            commands::install_agent,
            commands::download_apk,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
