# MediChat-RD 微信小程序架构方案

## 目标

第一版微信小程序不重写全站，而是围绕患者高频场景做一个轻量入口：

1. 患者中枢首页
2. DeepRare 轻量初筛
3. 病友社群欢迎房
4. 随访打卡
5. 我的 / provider 绑定态

## 关键原则

### 1. 账号主体系归平台自己

- 微信只负责登录入口
- 平台后端负责 `user_id / patient_id`
- `SecondMe` 只做可选 provider 绑定

### 2. Web 与小程序共用后端，不共用页面

- 现有 `FastAPI` 继续作为主业务后端
- 小程序独立目录：`apps/wechat-miniapp`
- 小程序 BFF 接口收敛到 `/api/v1/mp/*`

### 3. 首版只做原生高频动作

- 复杂工作台不搬进小程序
- 长流程和复杂图表先留在 Web
- 小程序聚焦轻操作、短反馈、强回访

## 目录

```text
apps/wechat-miniapp/
  src/
    pages/
      home/
      deeprare/
      community/
      checkin/
      profile/
    services/
      api.ts
      auth.ts

backend/
  mp_api.py
  mp_store.py
```

## BFF API

- `POST /api/v1/mp/auth/login`
- `GET /api/v1/mp/home`
- `POST /api/v1/mp/deeprare/submit`
- `GET /api/v1/mp/deeprare/result/{task_id}`
- `GET /api/v1/mp/community/feed`
- `POST /api/v1/mp/avatar/create`
- `GET /api/v1/mp/profile`
- `POST /api/v1/mp/followup/checkin`

## 微信侧上线前置

1. 配置小程序 `request` 合法域名：`https://medichatrd.cloud`
2. 如果要内嵌 H5，再配置业务域名
3. 准备 `code2Session` 所需的 `WECHAT_APP_ID / WECHAT_APP_SECRET`
4. 增加内容审核、举报和免责声明

## 后端环境变量

```env
WECHAT_APP_ID=你的微信小程序AppID
WECHAT_APP_SECRET=你的微信小程序AppSecret
```

如果这两个变量未配置，`/api/v1/mp/auth/login` 会继续用原型模式跑通前后端联调；一旦配置好，就会自动切到真实 `code2Session`。

## 第二阶段

等首版跑顺之后，再补：

- 原生化患者中枢更多模块
- 原生化社群发帖/回复
- 订阅消息提醒
- 随访计划
- SecondMe 绑定页
