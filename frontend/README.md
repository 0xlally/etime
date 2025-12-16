# ETime 前端项目

基于 React + Vite + TypeScript 构建的时间追踪系统前端。

## 项目结构

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API 客户端 (自动带 token, 401 跳转)
│   ├── components/            # 可复用组件
│   │   ├── CategorySelect.tsx
│   │   ├── TimerControls.tsx
│   │   ├── HeatmapGrid.tsx
│   │   ├── StatsChart.tsx
│   │   └── NotificationBell.tsx
│   ├── pages/                 # 页面组件
│   │   ├── Login.tsx          # 登录/注册页
│   │   ├── Timer.tsx          # 计时器页 (实时/手动)
│   │   ├── Stats.tsx          # 统计页 (今日/本周/本月/自定义)
│   │   ├── Heatmap.tsx        # 热力图页 (年度格子+明细弹窗)
│   │   ├── Targets.tsx        # 目标设置页
│   │   └── Admin.tsx          # 管理员页 (用户/会话/日志)
│   ├── types/
│   │   └── index.ts           # TypeScript 类型定义
│   ├── App.tsx                # 根组件 (路由配置)
│   ├── App.css                # 全局样式
│   ├── main.tsx               # 应用入口
│   └── index.css              # 基础样式
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 快速开始

### 安装依赖
```bash
cd frontend
npm install
```

### 开发模式
```bash
npm run dev
```
访问 http://localhost:3000

### 构建生产版本
```bash
npm run build
```

## 核心功能

### API 客户端
- **自动 Token 管理**: 自动在请求头添加 Bearer token
- **401 自动跳转**: 未认证时自动重定向到登录页
- **统一错误处理**: 集中处理 HTTP 错误

### 页面功能

#### 1. 登录页 (`/login`)
- 登录/注册切换
- 表单验证
- Token 存储到 localStorage

#### 2. 计时器页 (`/timer`)
- **实时计时**: 选择分类后开始/停止计时
- **手动补录**: 补录历史时间段
- 显示实时计时器

#### 3. 统计页 (`/stats`)
- 今日/本周/本月统计
- 自定义日期范围
- 分类占比饼图 (Recharts)

#### 4. 热力图页 (`/heatmap`)
- 年度格子热力图 (GitHub 风格)
- 点击某天弹出详细会话列表
- 颜色深度表示时长

#### 5. 目标设置页 (`/targets`)
- 创建目标 (日/周/月)
- 设置目标时长和包含分类
- 查看最近评估结果
- 启用/停用目标

#### 6. 管理员页 (`/admin`)
- **用户管理**: 搜索、启用/禁用用户
- **会话管理**: 多维度筛选、删除会话
- **审计日志**: 查看所有管理操作记录
- 分页支持

### 可复用组件

#### CategorySelect
```tsx
<CategorySelect value={categoryId} onChange={setCategoryId} />
```

#### TimerControls
```tsx
<TimerControls
  categoryId={categoryId}
  onSessionStart={() => {}}
  onSessionEnd={() => {}}
/>
```

#### HeatmapGrid
```tsx
<HeatmapGrid
  year={2024}
  data={heatmapData}
  onDayClick={(day) => {}}
/>
```

#### StatsChart
```tsx
<StatsChart
  data={[
    { name: '工作', value: 3600, color: '#3498db' },
    { name: '学习', value: 7200, color: '#2ecc71' }
  ]}
  title="分类占比"
/>
```

#### NotificationBell
```tsx
<NotificationBell />
```

## 技术栈

- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具 (快速 HMR)
- **React Router**: 路由管理
- **Axios**: HTTP 客户端
- **Recharts**: 图表库
- **date-fns**: 日期处理
- **lucide-react**: 图标库

## 项目特性

✅ **类型安全**: 完整的 TypeScript 类型定义  
✅ **组件化**: 高度可复用的组件设计  
✅ **路由保护**: ProtectedRoute 防止未登录访问  
✅ **自动认证**: API 客户端自动处理 token 和认证跳转  
✅ **响应式设计**: 现代化 CSS 布局  
✅ **开发体验**: Vite HMR + TypeScript IntelliSense

## API 代理配置

开发环境下，所有 `/api` 请求自动代理到 `http://localhost:8000`:

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

## 注意事项

1. **后端依赖**: 前端依赖后端 API，确保后端服务运行在 `http://localhost:8000`
2. **CORS**: 后端需配置 CORS 允许跨域请求
3. **Token 过期**: Token 过期时会自动跳转登录页
4. **管理员权限**: `/admin` 页面需要管理员角色
