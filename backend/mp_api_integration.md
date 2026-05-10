# Mini Program Router Integration

把微信小程序 BFF 接进现有 FastAPI 主应用时，只做两件事：

## 1. 在 `backend/main.py` 增加导入

```python
from .mp_api import router as mp_router
```

如果当前 `main.py` 不是包相对导入风格，则改成：

```python
from mp_api import router as mp_router
```

## 2. 在创建完 `app = FastAPI(...)` 且其他 API router 注册区附近加入

```python
app.include_router(mp_router)
```

## 不要做的事

- 不要把微信登录逻辑混进现有网页 OAuth 会话
- 不要直接复用 SecondMe 作为主身份体系
- 不要把小程序页面直接塞回现有 React Web 前端

## 下一步

1. 接入真实 `code2Session`
2. 把 `mp_store.py` 的会话和患者关系接到现有用户表/患者表
3. 把 `deeprare submit` 从当前原型返回，换成真实编排器调用
