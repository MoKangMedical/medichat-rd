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

如果要指定后端地址，可在启动前设置：

```bash
export TARO_APP_API_BASE=http://127.0.0.1:8001/api/v1/mp
```

## 需要的后端接口

默认对接 `https://medichatrd.cloud/api/v1/mp`，由 `backend/mp_api.py` 提供。

## 微信登录联调

- 后端未配置 `WECHAT_APP_ID / WECHAT_APP_SECRET` 时，登录接口会退回原型模式，便于先联通 UI 和业务流程。
- 配置真实微信参数后，会自动切到 `code2Session`。
