use rein_ch01_helloworld::rein::context_methods::{run, Index, Tasks};
use std::{env, fs, path::PathBuf};

#[tokio::main]
async fn main() {
    if let Err(error) = main_result().await {
        eprintln!("{error}");
        std::process::exit(2);
    }
}
async fn main_result() -> Result<(), String> {
    let argv: Vec<_> = env::args().collect();
    let strategy = argv
        .windows(2)
        .find(|pair| pair[0] == "--strategy")
        .map(|pair| pair[1].as_str())
        .unwrap_or("on-demand");
    let mut root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("fixtures/ch08-context");
    let mut budget = None;
    for i in 0..argv.len() {
        if argv[i] == "--data-root" {
            root = PathBuf::from(argv.get(i + 1).ok_or("--data-root requires a path")?)
        }
        if argv[i] == "--budget" {
            budget = Some(
                argv.get(i + 1)
                    .ok_or("--budget requires a number")?
                    .parse::<usize>()
                    .map_err(|_| "invalid budget")?,
            )
        }
    }
    let index: Index = serde_json::from_str(
        &fs::read_to_string(root.join("index.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let tasks: Tasks = serde_json::from_str(
        &fs::read_to_string(root.join("tasks.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let out = run(index, tasks, root, strategy, budget, None).await?;
    println!("{}", serde_json::to_string(&out).unwrap());
    Ok(())
}
