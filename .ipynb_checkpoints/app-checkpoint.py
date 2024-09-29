import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import warnings
warnings.filterwarnings('ignore')
from collections import defaultdict

import pandas as pd
from .baseline import Model

model = Model()


class Request(BaseModel):
    question: str


class Response(BaseModel):
    answer: str
    class_1: str
    class_2: str

app = FastAPI()


@app.get("/")
def index():
    return {"text": "Интеллектуальный помощник оператора службы поддержки."}

    
@app.post("/predict")
async def predict_sentiment(request: Request):
    result = model(request.question)
    response = Response(**result)
    return response

if __name__ == "__main__":
    host = "0.0.0.0" # Сконфигурируйте host согласно настройкам вашего сервера.
    config = uvicorn.Config(app, host=host, port=8000)
    server = uvicorn.Server(config)
    loop = asyncio.get_running_loop()
    loop.create_task(server.serve())
