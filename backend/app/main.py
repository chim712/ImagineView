from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .service.weather import WeatherService

import os
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용자님의 기상청 API 허브 인증키 (authKey)
WEATHER_KEY = os.getenv("WEATHER_KEY")
weather_service = WeatherService(WEATHER_KEY)

@app.get("/api/weather")
async def read_weather():
    # 충청남도 아산시 격자 좌표 (nx=60, ny=110)
    return weather_service.get_weather(nx=60, ny=110)