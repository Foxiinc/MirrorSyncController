use crate::models::{DeviceCommand, DeviceResponse, ScreenshotResult, TimeSyncResponse};
use base64::{engine::general_purpose, Engine as _};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::net::TcpStream;
use tokio::time::timeout;

const IO_TIMEOUT: Duration = Duration::from_secs(5);
const MAX_SCREENSHOT_SIZE: usize = 10 * 1024 * 1024;

pub struct AgentConnection {
    reader: BufReader<tokio::io::ReadHalf<TcpStream>>,
    writer: tokio::io::WriteHalf<TcpStream>,
    sequence: i32,
}

impl AgentConnection {
    pub async fn connect(host: &str, port: u16) -> Result<Self, String> {
        let addr = format!("{host}:{port}");
        let stream = timeout(IO_TIMEOUT, TcpStream::connect(&addr))
            .await
            .map_err(|_| format!("Connection timeout to {addr}"))?
            .map_err(|e| format!("Failed to connect to {addr}: {e}"))?;

        let (read_half, write_half) = tokio::io::split(stream);

        Ok(Self {
            reader: BufReader::new(read_half),
            writer: write_half,
            sequence: 0,
        })
    }

    pub async fn ping(&mut self) -> Result<(), String> {
        let msg = serde_json::json!({"type": "PING"});
        self.send_line(&msg.to_string()).await?;
        let _response = self.read_line().await?;
        Ok(())
    }

    pub async fn sync_time(&mut self) -> Result<i64, String> {
        let now = now_ms();
        let msg = serde_json::json!({
            "type": "TIME_SYNC",
            "client_time": now
        });
        self.send_line(&msg.to_string()).await?;
        let response = self.read_line().await?;
        let ts: TimeSyncResponse =
            serde_json::from_str(&response).map_err(|e| format!("Bad time sync response: {e}"))?;
        Ok(ts.offset())
    }

    pub async fn send_command(&mut self, cmd: &DeviceCommand) -> Result<DeviceResponse, String> {
        let json = serde_json::to_string(cmd).map_err(|e| format!("Serialize error: {e}"))?;
        self.send_line(&json).await?;
        let response = self.read_line().await?;
        serde_json::from_str(&response).map_err(|e| format!("Bad command response: {e}"))
    }

    pub async fn get_screenshot(&mut self) -> Result<ScreenshotResult, String> {
        let msg = serde_json::json!({"type": "SCREENSHOT"});
        self.send_line(&msg.to_string()).await?;

        let mut header = [0u8; 12];
        timeout(IO_TIMEOUT, self.reader.read_exact(&mut header))
            .await
            .map_err(|_| "Screenshot header timeout".to_string())?
            .map_err(|e| format!("Failed to read screenshot header: {e}"))?;

        let size = read_i32_be(&header[0..4]) as usize;
        let width = read_i32_be(&header[4..8]);
        let height = read_i32_be(&header[8..12]);

        if size == 0 || size > MAX_SCREENSHOT_SIZE {
            return Err(format!("Invalid screenshot size: {size}"));
        }

        let mut data = vec![0u8; size];
        timeout(Duration::from_secs(10), self.reader.read_exact(&mut data))
            .await
            .map_err(|_| "Screenshot data timeout".to_string())?
            .map_err(|e| format!("Failed to read screenshot data: {e}"))?;

        let base64 = general_purpose::STANDARD.encode(&data);

        Ok(ScreenshotResult {
            base64,
            width,
            height,
        })
    }

    pub fn next_sequence(&mut self) -> i32 {
        self.sequence += 1;
        self.sequence
    }

    async fn send_line(&mut self, data: &str) -> Result<(), String> {
        let mut buf = data.as_bytes().to_vec();
        buf.push(b'\n');
        timeout(IO_TIMEOUT, self.writer.write_all(&buf))
            .await
            .map_err(|_| "Write timeout".to_string())?
            .map_err(|e| format!("Write error: {e}"))
    }

    async fn read_line(&mut self) -> Result<String, String> {
        let mut line = String::new();
        timeout(IO_TIMEOUT, self.reader.read_line(&mut line))
            .await
            .map_err(|_| "Read timeout".to_string())?
            .map_err(|e| format!("Read error: {e}"))?;
        Ok(line.trim_end().to_string())
    }
}

fn read_i32_be(buf: &[u8]) -> i32 {
    ((buf[0] as i32) << 24) | ((buf[1] as i32) << 16) | ((buf[2] as i32) << 8) | (buf[3] as i32)
}

fn now_ms() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}
