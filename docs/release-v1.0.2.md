# ETime v1.0.2

本次发布聚焦首页计时体验、Android 可用性和项目文档展示。

## Highlights

- 计时首页重新整理布局：今日剩余放在右上角，常用卡片放在计时器上方，计时器按比例放大但保持手机首屏可用。
- 常用卡片和计时器主卡统一宽度，分类选择行去掉多余编辑预览，位置更稳定。
- Android 登录/API 地址修复后，生产 API 打包可直接连接线上服务。
- README 和推广文档全面更新，补充计时、计划、目标、复盘、分享、小组和 Android 自律模式介绍。
- 新增一组真实前端截图，覆盖桌面端、移动端和自律模式。

## Android

本次 Release 附带 APK：

- `etime-v1.0.2-release.apk`

如系统提示安装风险，请确认来源后继续安装。自律模式需要手动授予 Android “使用情况访问”和“悬浮窗”权限。

## Verification

- `cd frontend && npm run build`
- `cd frontend && npm run android:sync`
- `cd frontend/android && .\gradlew.bat assembleRelease`
- 使用 Playwright 生成并检查 README 截图。
