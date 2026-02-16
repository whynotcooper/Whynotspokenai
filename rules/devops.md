# DevOps Rules

## 技术栈
- **容器化**: Docker / Docker Compose
- **CI/CD**: GitHub Actions / GitLab CI
- **云服务**: Vercel / Railway / AWS
- **监控**: LogRocket / Sentry
- **域名**: DNS 配置

## Docker 配置

### Dockerfile
```dockerfile
# 多阶段构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - NODE_ENV=production
    
  backend:
    build: ./backend
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://...
    depends_on:
      - postgres
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## CI/CD 流程

### GitHub Actions
```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci
      - run: npm run test
      - run: npm run build
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: npm run deploy
```

## 环境配置

### 环境变量
```
# .env.production
NODE_ENV=production
DATABASE_URL=postgresql://...
API_URL=https://api.example.com
```

### 配置文件
```json
{
  "production": {
    "apiBaseUrl": "https://api.myapp.com",
    "features": {
      "analytics": true,
      "errorTracking": true
    }
  }
}
```

## 部署平台

### Vercel (前端)
```bash
# 自动部署
vercel --prod
```

### Railway (全栈)
```bash
# 部署后端
railway up
```

## 任务示例

### 配置部署
```
使用 Vercel 部署前端项目：
- 自动构建
- 环境变量配置
- 自定义域名
- HTTPS 证书
```

### 设置 CI/CD
```
配置 GitHub Actions：
- 自动化测试
- 代码检查
- 自动构建
- 部署到生产环境
```

### 监控配置
```
集成 Sentry 错误监控：
- 收集错误堆栈
- 设置告警
- 集成 Slack 通知
- 配置错误级别过滤
```

## 最佳实践
- 使用语义化版本
- 保持环境一致性
- 自动化一切
- 监控关键指标
- 定期备份数据
