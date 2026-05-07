use crate::adb;
use crate::agent::AgentConnection;
use crate::config::AppConfig;
use crate::models::*;
use std::collections::HashMap;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::process::Child;

pub struct DeviceManager {
    devices: HashMap<String, AndroidDevice>,
    connections: HashMap<String, AgentConnection>,
    mirrors: HashMap<String, Child>,
    adb_path: Option<String>,
    config: AppConfig,
    last_scan: Option<Instant>,
}

impl DeviceManager {
    pub async fn new(config: AppConfig) -> Self {
        let adb_path = adb::find_adb(&config.adb_paths).await;
        if let Some(ref p) = adb_path {
            tracing::info!("ADB found at: {p}");
        } else {
            tracing::warn!("ADB not found — device scanning will be unavailable");
        }

        Self {
            devices: HashMap::new(),
            connections: HashMap::new(),
            mirrors: HashMap::new(),
            adb_path,
            config,
            last_scan: None,
        }
    }

    pub async fn scan_devices(&mut self) -> Vec<DeviceInfo> {
        if let Some(last) = self.last_scan {
            if last.elapsed() < Duration::from_millis(self.config.scan_interval_ms) {
                return self.device_list();
            }
        }
        self.last_scan = Some(Instant::now());

        let adb_path = match &self.adb_path {
            Some(p) => p.clone(),
            None => return self.device_list(),
        };

        let adb_devices = adb::list_devices(&adb_path).await;
        let mut seen = std::collections::HashSet::new();

        for adb_dev in &adb_devices {
            if adb_dev.state != "device" {
                continue;
            }
            seen.insert(adb_dev.serial.clone());

            let is_new = !self.devices.contains_key(&adb_dev.serial);
            let device = self
                .devices
                .entry(adb_dev.serial.clone())
                .or_insert_with(|| AndroidDevice {
                    serial: adb_dev.serial.clone(),
                    port: self.config.agent_port,
                    status: "connected".to_string(),
                    ..Default::default()
                });

            if is_new || device.model.is_empty() {
                device.model = adb::get_device_model(&adb_path, &device.serial).await;
            }

            device.status = "connected".to_string();

            adb::setup_port_forward(&adb_path, &device.serial, self.config.agent_port).await;

            if !self.connections.contains_key(&adb_dev.serial) {
                self.try_connect_agent(&adb_dev.serial).await;
            }
        }

        let stale: Vec<String> = self
            .devices
            .keys()
            .filter(|s| !seen.contains(*s))
            .cloned()
            .collect();

        for serial in stale {
            self.disconnect_agent(&serial);
            self.devices.remove(&serial);
        }

        self.device_list()
    }

    async fn try_connect_agent(&mut self, serial: &str) {
        match AgentConnection::connect("127.0.0.1", self.config.agent_port).await {
            Ok(mut conn) => {
                if conn.ping().await.is_ok() {
                    let offset = conn.sync_time().await.unwrap_or(0);
                    if let Some(dev) = self.devices.get_mut(serial) {
                        dev.agent_connected = true;
                        dev.time_offset_ms = offset;
                        dev.last_ping_ms = now_ms();
                    }
                    self.connections.insert(serial.to_string(), conn);
                    tracing::info!("Agent connected on {serial}");
                } else {
                    tracing::debug!("Agent ping failed on {serial}");
                    if let Some(dev) = self.devices.get_mut(serial) {
                        dev.agent_connected = false;
                    }
                }
            }
            Err(e) => {
                tracing::debug!("Agent connection failed on {serial}: {e}");
                if let Some(dev) = self.devices.get_mut(serial) {
                    dev.agent_connected = false;
                }
            }
        }
    }

    fn disconnect_agent(&mut self, serial: &str) {
        self.connections.remove(serial);
        if let Some(dev) = self.devices.get_mut(serial) {
            dev.agent_connected = false;
        }
    }

    pub async fn send_command(
        &mut self,
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
    ) -> CommandResult {
        let targets = if target_devices.is_empty() {
            self.devices.keys().cloned().collect::<Vec<_>>()
        } else {
            target_devices
        };

        let exec_time = now_ms() + self.config.sync_delay_ms as i64;
        let mut success_count = 0;
        let total = targets.len();

        for serial in &targets {
            let time_offset = self
                .devices
                .get(serial)
                .map(|d| d.time_offset_ms)
                .unwrap_or(0);

            let conn = match self.connections.get_mut(serial) {
                Some(c) => c,
                None => continue,
            };

            let cmd = DeviceCommand {
                sequence: conn.next_sequence(),
                cmd_type: cmd_type.clone(),
                x,
                y,
                end_x,
                end_y,
                duration_ms,
                text: text.clone(),
                key_code,
                exec_time_device_ms: exec_time + time_offset,
                tap_view_id: tap_view_id.clone(),
                tap_text: tap_text.clone(),
                tap_content_desc: tap_content_desc.clone(),
            };

            match conn.send_command(&cmd).await {
                Ok(resp) if resp.success => {
                    success_count += 1;
                }
                Ok(resp) => {
                    tracing::warn!("Command failed on {serial}: {}", resp.message);
                }
                Err(e) => {
                    tracing::error!("Command error on {serial}: {e}");
                    self.mark_disconnected(serial);
                }
            }
        }

        CommandResult {
            success: success_count > 0,
            message: format!("{success_count}/{total} devices ok"),
            devices_count: total,
        }
    }

    pub async fn get_screenshot(&mut self, serial: &str) -> Result<ScreenshotResult, String> {
        let conn = self
            .connections
            .get_mut(serial)
            .ok_or_else(|| format!("No connection to {serial}"))?;

        conn.get_screenshot().await
    }

    pub async fn start_mirror(&mut self, serial: &str) -> Result<(), String> {
        if !self.devices.contains_key(serial) {
            return Err("Device not found".to_string());
        }

        if self.mirrors.contains_key(serial) {
            return Ok(());
        }

        // Агрессивный профиль: максимум FPS/качество, минимальная задержка.
        let child = tokio::process::Command::new("scrcpy")
            .args([
                "-s",
                serial,
                "--bit-rate",
                "16M",
                "--max-fps",
                "60",
                "--no-vsync",
                "--turn-screen-off",
                &format!("--window-title=Mirror-{serial}"),
            ])
            .spawn()
            .map_err(|e| format!("Failed to start scrcpy: {e}"))?;

        tracing::info!("Mirror started for {serial}");
        self.mirrors.insert(serial.to_string(), child);
        Ok(())
    }

    pub async fn stop_mirror(&mut self, serial: &str) -> Result<(), String> {
        if let Some(mut child) = self.mirrors.remove(serial) {
            let _ = child.kill().await;
            tracing::info!("Mirror stopped for {serial}");
        }
        Ok(())
    }

    pub async fn install_agent(&self, serial: &str) -> InstallResult {
        let adb_path = match &self.adb_path {
            Some(p) => p.clone(),
            None => {
                return InstallResult {
                    success: false,
                    message: "ADB not found".to_string(),
                }
            }
        };

        // Ищем APK в таком порядке:
        // 1) Путь явно задан в конфиге.
        // 2) В текущей рабочей директории (drm/launcher могут положить туда).
        // 3) Рядом с бинарником (dev/standalone случай).
        let apk_path = if let Some(p) = &self.config.agent_apk_path {
            p.clone()
        } else if let Ok(cwd) = std::env::current_dir() {
            let candidate = cwd.join("agent.apk");
            if candidate.exists() {
                candidate.to_string_lossy().to_string()
            } else {
                std::env::current_exe()
                    .ok()
                    .and_then(|p| {
                        p.parent()
                            .map(|d| d.join("agent.apk").to_string_lossy().to_string())
                    })
                    .unwrap_or_else(|| "agent.apk".to_string())
            }
        } else {
            std::env::current_exe()
                .ok()
                .and_then(|p| {
                    p.parent()
                        .map(|d| d.join("agent.apk").to_string_lossy().to_string())
                })
                .unwrap_or_else(|| "agent.apk".to_string())
        };

        if !std::path::Path::new(&apk_path).exists() {
            return InstallResult {
                success: false,
                message: format!("APK not found: {apk_path}"),
            };
        }

        let (success, message) = adb::install_apk(&adb_path, serial, &apk_path).await;
        InstallResult { success, message }
    }

    fn device_list(&self) -> Vec<DeviceInfo> {
        self.devices.values().map(|d| d.to_info()).collect()
    }

    fn mark_disconnected(&mut self, serial: &str) {
        self.connections.remove(serial);
        if let Some(dev) = self.devices.get_mut(serial) {
            dev.agent_connected = false;
        }
    }
}

fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}
