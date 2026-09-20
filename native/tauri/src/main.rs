use base64::{engine::general_purpose::STANDARD, Engine};
use serde_json::{json, Value};
use std::{fs, path::{Component, PathBuf}, sync::Mutex, time::UNIX_EPOCH};

struct Ports { root: PathBuf, history: Mutex<(Vec<Value>, usize)> }
#[tauri::command]
fn port(request: Value, state: tauri::State<Ports>) -> Result<Value, String> {
    let op = request["op"].as_str().ok_or("missing operation")?;
    match op {
        "root" => return Ok(json!({"name":state.root.file_name().unwrap_or_default().to_string_lossy()})),
        "route" => {
            let mut history = state.history.lock().map_err(|e| e.to_string())?;
            let location = request["state"].clone();
            let index = history.1;
            if request["replace"] == true && !history.0.is_empty() { history.0[index] = location; }
            else { history.0.truncate(index + 1); history.0.push(location); history.1 = history.0.len()-1; }
            return Ok(Value::Null)
        },
        "navigate" => {
            let mut history = state.history.lock().map_err(|e| e.to_string())?;
            let delta = request["delta"].as_i64().ok_or("missing delta")?;
            if ![-1,1].contains(&delta) { return Err("invalid delta".into()); }
            if history.0.is_empty() { return Ok(Value::Null); }
            history.1 = (history.1 as i64 + delta).clamp(0, history.0.len() as i64-1) as usize;
            return Ok(history.0[history.1].clone())
        },
        _ => {}
    }
    let relative = request["path"].as_str().ok_or("missing path")?;
    let mut path = state.root.clone();
    for component in std::path::Path::new(relative).components() {
        if let Component::Normal(name) = component { path.push(name); }
        else { return Err("invalid path".into()); }
        if fs::symlink_metadata(&path).map_err(|e| e.to_string())?.file_type().is_symlink() { return Err("symlink refused".into()); }
    }
    let metadata = fs::metadata(&path).map_err(|e|e.to_string())?;
    match op {
        "list" => {
            let mut entries = Vec::new();
            for entry in fs::read_dir(path).map_err(|e|e.to_string())? {
                let entry = entry.map_err(|e|e.to_string())?;
                let kind = entry.file_type().map_err(|e|e.to_string())?;
                if !kind.is_file() && !kind.is_dir() { continue; }
                let name = entry.file_name().to_string_lossy().to_string();
                entries.push(json!({"name":name,"path":if relative.is_empty(){name.clone()}else{format!("{relative}/{name}")},"dir":kind.is_dir()}));
            }
            Ok(json!(entries))
        },
        "stat" => Ok(json!({"size":metadata.len(),"mod":metadata.modified().map_err(|e|e.to_string())?.duration_since(UNIX_EPOCH).map_err(|e|e.to_string())?.as_millis(),"type":""})),
        "read" if metadata.is_file() => Ok(json!(STANDARD.encode(fs::read(path).map_err(|e|e.to_string())?))),
        "write" if metadata.is_file() => { fs::write(path,request["text"].as_str().ok_or("missing text")?).map_err(|e|e.to_string())?; Ok(Value::Null) },
        _ => Err("invalid operation".into())
    }
}
fn main() {
    let root = std::env::var_os("FILEMILL_ROOT").or_else(||std::env::args_os().nth(1)).expect("directory argument required");
    tauri::Builder::default().manage(Ports{root:fs::canonicalize(root).expect("directory"),history:Mutex::new((Vec::new(),0))})
        .invoke_handler(tauri::generate_handler![port])
        .run(tauri::generate_context!()).expect("native shell");
}
