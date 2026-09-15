type DemoState = 'running' | 'completed' | 'failed' | 'paused'

function label(state: DemoState): string {
  switch (state) {
    case 'running': return '进行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'paused': return '暂停'
  }
}
console.log(label('completed'))
