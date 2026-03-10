use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceInfo {
    pub serial: String,
    pub model: String,
    pub status: String,
    pub agent_connected: bool,
    pub port: u16,
}

#[derive(Debug, Clone, Default)]
pub struct AndroidDevice {
    pub serial: String,
    pub model: String,
    pub status: String,
    pub agent_connected: bool,
    pub port: u16,
    pub time_offset_ms: i64,
    pub last_ping_ms: i64,
}

impl AndroidDevice {
    pub fn to_info(&self) -> DeviceInfo {
        DeviceInfo {
            serial: self.serial.clone(),
            model: self.model.clone(),
            status: self.status.clone(),
            agent_connected: self.agent_connected,
            port: self.port,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceCommand {
    #[serde(rename = "seq")]
    pub sequence: i32,
    #[serde(rename = "type")]
    pub cmd_type: String,
    #[serde(default)]
    pub x: f32,
    #[serde(default)]
    pub y: f32,
    #[serde(default)]
    pub end_x: f32,
    #[serde(default)]
    pub end_y: f32,
    #[serde(default)]
    pub duration_ms: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text: Option<String>,
    #[serde(default)]
    pub key_code: i32,
    #[serde(default)]
    pub exec_time_device_ms: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tap_view_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tap_text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tap_content_desc: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeviceResponse {
    #[serde(rename = "seq", default)]
    pub sequence: i32,
    #[serde(default)]
    pub success: bool,
    #[serde(default)]
    pub message: String,
    #[serde(rename = "executed_at_ms", default)]
    pub executed_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenshotResult {
    pub base64: String,
    pub width: i32,
    pub height: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub message: String,
    pub devices_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstallResult {
    pub success: bool,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeSyncResponse {
    #[serde(rename = "client_time", default)]
    pub client_time: i64,
    #[serde(rename = "server_time", default)]
    pub server_time: i64,
    #[serde(rename = "round_trip_time", default)]
    pub round_trip_time: i64,
}

impl TimeSyncResponse {
    pub fn offset(&self) -> i64 {
        self.server_time - self.client_time - (self.round_trip_time / 2)
    }
}
