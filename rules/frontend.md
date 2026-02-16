# Frontend Development Rules

## 技术栈
- **Framework**: React 18+ 或 Vue 3+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite

## 代码规范

### 组件开发
- 使用函数式组件 + Hooks
- 组件文件命名: `PascalCase.tsx`
- 遵循单一职责原则
- 提取可复用的 UI 组件

### 样式设计
- 使用 Tailwind CSS Utility 类
- 移动优先 (Mobile First)
- 实现响应式设计 ( breakpoints: sm, md, lg, xl )
- 使用 CSS 变量管理主题

### 状态管理
- 局部状态: useState, useReducer
- 全局状态: Zustand / Pinia
- 服务状态: React Query / TanStack Query

### 目录结构
```
src/
├── components/
│   ├── ui/          # 基础 UI 组件
│   ├── layout/      # 布局组件
│   └── features/    # 功能组件
├── pages/           # 页面组件
├── hooks/           # 自定义 Hooks
├── utils/           # 工具函数
├── styles/          # 全局样式
└── types/           # TypeScript 类型
```

## 任务示例

### 创建页面
```
创建首页，包含：
- Hero 区域 (标题 + CTA 按钮)
- 特性展示区 (3 列卡片)
- 页脚
使用 Tailwind CSS 实现响应式布局
```

### 创建组件
```
创建一个按钮组件：
- 支持 primary/secondary/outline 样式
- 支持 sizes: sm, md, lg
- 支持 disabled 状态
- 包含 loading 状态
```

### 实现功能
```
实现用户登录表单：
- 邮箱验证
- 密码强度检查
- 显示/隐藏密码
- 表单提交状态
- 错误提示
```

## 测试要求
- 组件单元测试 (Vitest + React Testing Library)
- E2E 测试 (Playwright)
- 覆盖率 > 80%
