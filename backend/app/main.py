from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from .service.weather import WeatherService

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

@app.get("/api/weather/debug", response_class=PlainTextResponse)
async def debug_weather():
    """사람이 읽기 좋은 형태로 기상청 Raw 데이터를 출력"""
    return weather_service.get_debug_text(nx=60, ny=110)



# dist 경로 지정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "../../frontend/dist")

# 정적 파일 mount
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

# 루트 페이지
@app.get("/")
async def serve_react():
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))