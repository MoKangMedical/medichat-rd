# MediChat-RD 微信小程序前端壳

这个目录是独立于现有 Web 前端的微信小程序工程，采用 **Taro + React**。

## 首版目标

- 患者中枢首页
- DeepRare 轻量初筛
- 病友社群欢迎房
- 随访打卡
- 个人页 / provider 绑定态展示

## 为什么不直接复用 Web 前端

现有 Web 前端更适合复杂工作台；微信小程序适合高频、轻量、强回访的患者动作。两者共享业务流程和 API，不共享页面实现。

## 本地开发

```bash
cd apps/wechat-miniapp
npm install
npm run dev:weapp
```

## 需要的后端接口

默认对接 `https://medichatrd.cloud/api/v1/mp`，由 `backend/mp_api.py` 提供。
