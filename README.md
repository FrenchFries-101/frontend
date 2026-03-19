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