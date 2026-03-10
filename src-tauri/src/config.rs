use serde::{Deserialize, Serialize};
use std::path::PathBuf;

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
        }
    }
}

impl AppConfig {
    pub fn load() -> Self {
        let locations = [
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.join("config.json"))),
            Some(PathBuf::from("config.json")),
        ];

        for loc in locations.iter().flatten() {
            if loc.exists() {
                if let Ok(data) = std::fs::read_to_string(loc) {
                    match serde_json::from_str::<AppConfig>(&data) {
                        Ok(cfg) => {
                            tracing::info!("Config loaded from {}", loc.display());
                            return cfg;
                        }
                        Err(e) => {
                            tracing::warn!("Failed to parse {}: {}", loc.display(), e);
                        }
                    }
                }
            }
        }

        tracing::info!("Using default config");
        AppConfig::default()
    }
}
