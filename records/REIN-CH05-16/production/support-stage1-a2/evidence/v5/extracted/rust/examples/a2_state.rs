enum DemoState {
    Running,
    Completed,
    Failed,
    Paused,
}

fn label(state: &DemoState) -> &'static str {
    match state {
        DemoState::Running => "进行中",
        DemoState::Completed => "已完成",
        DemoState::Failed => "失败",
        DemoState::Paused => "暂停",
    }
}
fn main() {
    println!("{}", label(&DemoState::Completed));
}
