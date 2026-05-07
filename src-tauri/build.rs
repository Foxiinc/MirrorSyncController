fn main() {
    if std::env::var("CARGO_CFG_TARGET_OS").ok().as_deref() == Some("windows") {
        let windows = tauri_build::WindowsAttributes::new()
            .app_manifest(include_str!("windows.manifest"));
        tauri_build::try_build(tauri_build::Attributes::new().windows_attributes(windows))
            .expect("tauri build failed");
    } else {
        tauri_build::build();
    }
}
