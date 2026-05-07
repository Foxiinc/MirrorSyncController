use std::path::PathBuf;
use tokio::process::Command;

#[derive(Debug)]
pub struct AdbDevice {
    pub serial: String,
    pub state: String,
}

pub async fn find_adb(extra_paths: &[String]) -> Option<String> {
    for p in extra_paths {
        if !p.is_empty() && PathBuf::from(p).exists() {
            return Some(p.clone());
        }
    }

    // 1) Попробуем просто запустить `adb` из PATH.
    if let Ok(output) = Command::new("adb").arg("version").output().await {
        if output.status.success() {
            // Если команда прошла — можно использовать просто "adb" как имя бинарника.
            return Some("adb".to_string());
        }
    }

    // 2) Дополнительные OS‑специфичные пути и утилиты (`which`/`where`) как fallback.
    #[cfg(not(target_os = "windows"))]
    {
        if let Ok(output) = Command::new("which").arg("adb").output().await {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        if let Ok(output) = Command::new("where").arg("adb").output().await {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout)
                    .lines()
                    .next()
                    .unwrap_or("")
                    .trim()
                    .to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
    }

    let fallbacks = if cfg!(target_os = "windows") {
        vec![
            r"C:\platform-tools\adb.exe".to_string(),
            r"C:\Android\Sdk\platform-tools\adb.exe".to_string(),
            format!(
                r"{}\Android\Sdk\platform-tools\adb.exe",
                std::env::var("LOCALAPPDATA").unwrap_or_default()
            ),
        ]
    } else {
        let home = std::env::var("HOME").unwrap_or_default();
        vec![
            format!("{home}/Android/Sdk/platform-tools/adb"),
            "/usr/bin/adb".to_string(),
            "/usr/local/bin/adb".to_string(),
        ]
    };

    for p in &fallbacks {
        if PathBuf::from(p).exists() {
            return Some(p.clone());
        }
    }

    None
}

pub async fn list_devices(adb_path: &str) -> Vec<AdbDevice> {
    let output = match Command::new(adb_path).arg("devices").output().await {
        Ok(o) => o,
        Err(e) => {
            tracing::error!("Failed to run adb devices: {e}");
            return vec![];
        }
    };

    if !output.status.success() {
        tracing::warn!("adb devices exited with {}", output.status);
        return vec![];
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    stdout
        .lines()
        .skip(1) // skip "List of devices attached"
        .filter_map(|line| {
            let line = line.trim();
            if line.is_empty() {
                return None;
            }
            let mut parts = line.split_whitespace();
            let serial = parts.next()?.to_string();
            let state = parts.next().unwrap_or("unknown").to_string();
            Some(AdbDevice { serial, state })
        })
        .collect()
}

pub async fn get_device_model(adb_path: &str, serial: &str) -> String {
    let output = Command::new(adb_path)
        .args(["-s", serial, "shell", "getprop", "ro.product.model"])
        .output()
        .await;

    match output {
        Ok(o) if o.status.success() => {
            let model = String::from_utf8_lossy(&o.stdout).trim().to_string();
            if model.is_empty() { "Unknown".to_string() } else { model }
        }
        _ => "Unknown".to_string(),
    }
}

pub async fn setup_port_forward(adb_path: &str, serial: &str, port: u16) -> bool {
    let port_str = port.to_string();
    let result = Command::new(adb_path)
        .args([
            "-s", serial, "forward",
            &format!("tcp:{port_str}"),
            &format!("tcp:{port_str}"),
        ])
        .output()
        .await;

    match result {
        Ok(o) => {
            if !o.status.success() {
                tracing::warn!(
                    "Port forward failed for {serial}: {}",
                    String::from_utf8_lossy(&o.stderr)
                );
            }
            o.status.success()
        }
        Err(e) => {
            tracing::error!("Port forward error for {serial}: {e}");
            false
        }
    }
}

pub async fn install_apk(adb_path: &str, serial: &str, apk_path: &str) -> (bool, String) {
    let result = Command::new(adb_path)
        .args(["-s", serial, "install", "-r", apk_path])
        .output()
        .await;

    match result {
        Ok(o) => {
            let stdout = String::from_utf8_lossy(&o.stdout).to_string();
            let stderr = String::from_utf8_lossy(&o.stderr).to_string();
            if o.status.success() {
                (true, "Agent installed. Enable Accessibility Service on the device.".to_string())
            } else {
                let msg = if stderr.is_empty() { stdout } else { stderr };
                (false, msg.trim().to_string())
            }
        }
        Err(e) => (false, format!("Failed to run adb install: {e}")),
    }
}
