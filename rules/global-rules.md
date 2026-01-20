# 全局规则

## 读取类（总是允许）

### allow-read
- tool: Read
  action: allow
  reason: 读取文件总是安全的

### allow-glob
- tool: Glob
  action: allow
  reason: 搜索文件名安全

### allow-grep
- tool: Grep
  action: allow
  reason: 搜索内容安全

## 编辑类（允许）

### allow-write
- tool: Write
  action: allow
  reason: 写入文件是核心功能

### allow-edit
- tool: Edit
  action: allow
  reason: 编辑文件是核心功能

### allow-notebook-edit
- tool: NotebookEdit
  action: allow
  reason: 编辑笔记本是核心功能

## 网络类（允许）

### allow-web-search
- tool: WebSearch
  action: allow
  reason: 网络搜索安全

### allow-web-fetch
- tool: WebFetch
  action: allow
  reason: 获取网页安全

## Bash 命令

### 只读命令（允许）

### allow-readonly-bash
- tool: Bash
  action: allow
  pattern: ^(ls|pwd|cat|head|tail|wc|which|echo|date|whoami)\b
  reason: 只读命令

### allow-git-readonly
- tool: Bash
  action: allow
  pattern: ^git (status|log|diff|branch|remote|show|stash list)\b
  reason: Git 只读命令

### 测试和检查（允许）

### allow-test
- tool: Bash
  action: allow
  pattern: ^(npm test|npm run test|npm run lint|npm run check|pytest|go test|cargo test|bun test)
  reason: 测试和检查命令

### 危险命令（拒绝）

### deny-dangerous-rm
- tool: Bash
  action: deny
  pattern: rm\s+-rf\s+[/~]
  reason: 危险：可能删除重要目录

### deny-fork-bomb
- tool: Bash
  action: deny
  pattern: :\(\)\s*\{\s*:\|:&\s*\}\s*;:
  reason: 危险：Fork bomb

## 文件保护

### deny-env-files
- tool: Write|Edit
  action: deny
  path: "**/.env*"
  reason: 保护环境变量文件

### deny-credentials
- tool: Write|Edit
  action: deny
  path: "**/credentials*"
  reason: 保护凭证文件

## 其他

### allow-todo
- tool: TodoWrite
  action: allow
  reason: 写待办安全

### allow-ask
- tool: AskUserQuestion
  action: allow
  reason: 询问用户安全

### allow-task
- tool: Task
  action: allow
  reason: 启动子任务安全

### allow-skill
- tool: Skill
  action: allow
  reason: 调用技能安全
