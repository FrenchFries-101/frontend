# AgileProject
This repository is for the agile software engineering project.
Group 1: FrenchFries101
## requirement install 
* pyside6
* QT
---

## Use of API
1. /service/API.py
2. Currently, the interface functions for words and listening have been imported.
for example:
```python
from service.API import get_words
```
---
## 运行后端程序步骤
1. 添加main
```python
from fastapi import FastAPI
from routers import listening, word

app = FastAPI()

app.include_router(listening.router)
app.include_router(word.router)
```
2. 在终端运行
```
python models.py
```
3. 修改database.py(懒得配置mysql了)，把之前那句注释掉
```python
DATABASE_URL = "sqlite:///./test.db"
```
4. 在终端运行
```
python seed_data.py
```
5. 在终端运行
```
uvicorn main:app --reload
```
---
## 全局获取user_id
```python
import session
user_id = session.user["id"]
```

---
## 3.23 修复已知问题
1. 登录速度变快（在运行登录之前就预先加载界面）
2. 加 loading 动画，防止一下加载不出来数据
3. 主界面退出自动清空原先登录信息
4. 注册完不能直接登录，要返回登录界面