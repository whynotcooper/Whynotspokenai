# MiniMax Web Development Team

## 连接 MiniMax

运行以下命令连接 MiniMax：

```bash
/opencode
/connect
# 搜索 "MiniMax"
# 输入你的 API key
```

## 可用模型

- **minimax-m2.1** - 主模型 (200K context, 32K output)
- **minimax-m1** - 轻量模型 (100K context, 16K output)

## 团队代理

### 1. frontend - 前端开发
负责 HTML、CSS、JavaScript/TypeScript、React/Vue 组件、响应式设计

### 2. backend - 后端开发
负责 API 开发、数据库设计、服务器逻辑、业务逻辑

### 3. fullstack - 全栈协调
负责整体架构设计、前后端整合、项目协调

### 4. ui-designer - UI/UX 设计
负责页面布局、组件设计、用户体验优化

### 5. devops - 部署运维
负责 CI/CD、部署配置、服务器管理

## 使用方法

```bash
# 启动项目
cd your-web-project
opencode

# 查看团队成员
/agents

# 切换到前端开发
/agent frontend
创建一个响应式导航栏组件

# 切换到后端开发
/agent backend
创建用户认证 API

# 切换到全栈协调
/agent fullstack
整合前后端并测试

# 查看当前代理
/agent
```

## 项目结构

```
your-project/
├── src/
│   ├── components/     # React/Vue 组件
│   ├── pages/          # 页面
│   ├── api/            # API 接口
│   ├── utils/          # 工具函数
│   └── styles/         # 样式文件
├── public/             # 静态资源
├── tests/              # 测试文件
├── opencode.json       # 配置文件
└── AGENTS.md          # 团队配置
```
