use std::process::{Command, Child};
use std::thread;
use std::time::Duration;
use std::path::PathBuf;

static mut BACKEND_PROCESS: Option<Child> = None;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      start_backend_server();
      
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      
      Ok(())
    })
    .on_window_event(|_window, event| {
      if matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
        stop_backend_server();
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

fn start_backend_server() {
  thread::spawn(|| {
    let install_dir = find_install_dir();
    
    let python_paths = vec![
      install_dir.join("venv/bin/python3"),
      install_dir.join("venv/bin/python"),
      PathBuf::from("/opt/luna-os/venv/bin/python3"),
      PathBuf::from("/opt/luna-os/venv/bin/python"),
      PathBuf::from("python3"),
      PathBuf::from("python"),
    ];

    for python_path in python_paths.iter() {
      let cmd_str = python_path.to_string_lossy().to_string();
      
      match Command::new(&cmd_str)
        .arg("-m")
        .arg("uvicorn")
        .arg("backend.main:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("3000")
        .arg("--log-level")
        .arg("info")
        .current_dir(&install_dir)
        .env("PYTHONUNBUFFERED", "1")
        .spawn()
      {
        Ok(child) => {
          unsafe {
            BACKEND_PROCESS = Some(child);
          }
          thread::sleep(Duration::from_secs(4));
          return;
        }
        Err(_) => continue,
      }
    }
    
    eprintln!("Failed to start backend from: {:?}", install_dir);
  });
}

fn find_install_dir() -> PathBuf {
  if let Ok(exe) = std::env::current_exe() {
    if let Some(parent) = exe.parent() {
      if let Some(parent) = parent.parent() {
        if let Some(parent) = parent.parent() {
          if parent.join("backend").exists() {
            return parent.to_path_buf();
          }
        }
      }
    }
  }
  
  if let Ok(home) = std::env::var("HOME") {
    let user_dir = PathBuf::from(format!("{}/.local/opt/luna-os", home));
    if user_dir.exists() {
      return user_dir;
    }
  }
  
  let sys_dir = PathBuf::from("/opt/luna-os");
  if sys_dir.exists() {
    return sys_dir;
  }
  
  PathBuf::from(".")
}

fn stop_backend_server() {
  unsafe {
    if let Some(mut child) = BACKEND_PROCESS.take() {
      let _ = child.kill();
      let _ = child.wait();
    }
  }
}
