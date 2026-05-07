use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    #[serde(default = "default_agent_port")]
    pub agent_port: u16,
    #[serde(default = "default_max_devices")]
    pub max_devices: usize,
    #[serde(default = "default_scan_interval")]
    pub scan_interval_ms: u64,
    #[serde(default = "default_command_timeout")]
    pub command_timeout_ms: u64,
    #[serde(default = "default_sync_delay")]
    pub sync_delay_ms: u64,
    #[serde(default = "default_max_reconnect")]
    pub max_reconnect_attempts: u32,
    #[serde(default)]
    pub adb_paths: Vec<String>,
    #[serde(default)]
    pub agent_apk_path: Option<String>,
    /// Прямой URL до APK (например, GitHub Releases latest/download/agent.apk).
    /// Если не задан – команда download_apk вернёт ошибку.
    #[serde(default)]
    pub apk_download_url: Option<String>,
}

fn default_agent_port() -> u16 { 4444 }
fn default_max_devices() -> usize { 20 }
fn default_scan_interval() -> u64 { 5000 }
fn default_command_timeout() -> u64 { 5000 }
fn default_sync_delay() -> u64 { 50 }
fn default_max_reconnect() -> u32 { 5 }

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            agent_port: 4444,
            max_devices: 20,
            scan_interval_ms: 5000,
            command_timeout_ms: 5000,
            sync_delay_ms: 50,
            max_reconnect_attempts: 5,
            adb_paths: vec![],
            agent_apk_path: None,
            apk_download_url: None,
        }
    }
}

impl AppConfig {
    pub fn load() -> Self {
        // Конфиг вшит на этапе сборки.
        // Путь: src-tauri/src/ -> ../../config.json (корень репозитория).
        const EMBEDDED_CONFIG: &str = include_str!("../../config.json");

        match serde_json::from_str::<AppConfig>(EMBEDDED_CONFIG) {
            Ok(cfg) => {
                tracing::info!("Using embedded config.json");
                cfg
            }
            Err(e) => {
                tracing::warn!("Failed to parse embedded config.json: {e}, using defaults");
                AppConfig::default()
            }
        }
    }
}
