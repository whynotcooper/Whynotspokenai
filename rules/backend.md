# Backend Development Rules

## 技术栈
- **Runtime**: Node.js 18+ 或 Python 3.11+
- **Framework**: Express.js / FastAPI
- **Database**: PostgreSQL / MongoDB
- **ORM**: Prisma / SQLAlchemy

## 代码规范

### API 设计
- 遵循 RESTful 最佳实践
- 使用语义化 HTTP 方法
- 版本控制: `/api/v1/`
- 统一的响应格式

### 响应格式
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

### 错误处理
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "邮箱格式不正确",
    "details": [ ... ]
  }
}
```

### 目录结构
```
src/
├── controllers/     # 控制器
├── services/        # 业务逻辑
├── models/          # 数据模型
├── repositories/    # 数据访问层
├── middleware/      # 中间件
├── routes/          # 路由定义
├── utils/           # 工具函数
├── config/          # 配置文件
└── types/           # 类型定义
```

## 安全规范

### 认证授权
- JWT Token 认证
- RBAC 权限控制
- 敏感数据加密
- SQL 注入防护
- XSS 防护

### 输入验证
- 使用验证库 (Zod / Pydantic)
- 参数类型检查
- 范围限制
- 白名单校验

## 数据库设计

### PostgreSQL
- 使用 Prisma ORM
- 外键约束
- 索引优化
- 软删除 (deletedAt)

### MongoDB
- Mongoose ODM
- Schema 验证
- 复合索引
- 聚合管道

## 任务示例

### 创建 API
```
创建用户 API：
- POST /api/v1/users - 创建用户
- GET /api/v1/users/:id - 获取用户详情
- PUT /api/v1/users/:id - 更新用户
- DELETE /api/v1/users/:id - 删除用户
```

### 实现功能
```
实现用户认证：
- 用户注册 (邮箱验证)
- 登录 (JWT Token)
- Token 刷新
- 密码重置
- 权限验证中间件
```

### 数据库操作
```
创建文章管理功能：
- 文章 CRUD API
- 分类管理
- 标签管理
- 搜索功能
- 分页查询
```

## 测试要求
- 单元测试 (Jest / Pytest)
- 集成测试
- API 端点测试
- 覆盖率 > 80%
