# MiniMax Web Team - 快速开始指南

## 1. 连接 MiniMax

```bash
# 启动 OpenCode
opencode

# 在 OpenCode 中运行
/connect
# 搜索 "MiniMax"
# 输入你的 API key (从 platform.minimax.io 获取)
```

## 2. 选择模型

```bash
# 查看可用模型
/models

# 选择 MiniMax M2.1
minimax-minimax-m2.1
```

## 3. 初始化项目

```bash
# 进入项目目录
cd your-web-project

# 初始化 OpenCode
/init
```

## 4. 使用团队代理

### 方法 A: 通过 /agent 命令

```bash
# 查看所有代理
/agents

# 切换到前端开发
/agent frontend
创建首页组件

# 切换到后端开发
/agent backend
创建用户 API

# 切换到全栈协调
/agent fullstack
整合前后端
```

### 方法 B: 直接指定代理

```bash
# 使用前端代理
/agent frontend
设计响应式导航栏

# 使用后端代理
/agent backend
实现 JWT 认证

# 使用 UI 设计
/agent ui-designer
优化用户界面

# 使用 DevOps
/agent devops
配置 Docker 部署
```

## 5. 常用命令

```bash
/models          # 选择模型
/agents          # 查看代理列表
/agent [名称]    # 切换代理
/rules           # 查看当前规则
/undo            # 撤销更改
/redo            # 重做更改
/clear           # 清除对话
/exit            # 退出
```

## 6. 项目示例

### 创建新网站项目

```bash
/opencode
/agent fullstack
创建一个完整的网站项目，包括：
- React 前端 (首页、关于我们、联系页面)
- Express.js 后端 (用户认证、API 接口)
- PostgreSQL 数据库
- Docker 部署配置
```

### 添加新功能

```bash
/agent frontend
添加用户仪表盘页面，包含：
- 用户信息卡片
- 最近活动列表
- 设置选项

/agent backend
为仪表盘创建 API：
- GET /api/users/:id/profile
- GET /api/users/:id/activities
- PUT /api/users/:id/settings
```

## 7. 配置文件说明

主要配置文件:
- `opencode.json` - 主配置
- `TEAM.md` - 团队说明
- `rules/*.md` - 各角色规则

## 8. 注意事项

⚠️ **重要**:
- MiniMax API key 需要从 [MiniMax Platform](https://platform.minimax.io/) 获取
- 确保账户有足够的调用配额
- M2.1 适合复杂任务，M1 适合简单任务

💡 **建议**:
- 为不同任务选择合适的代理
- 使用 `/undo` 撤销不满意的更改
- 定期保存工作进度
