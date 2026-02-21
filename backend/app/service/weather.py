import requests
from datetime import datetime, timedelta


class WeatherService:
    def __init__(self, auth_key: str):
        self.auth_key = auth_key
        # 기상청 API 허브 단기예보 URL (TMN, TMX 포함)
        self.base_url = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst"

    def _get_base_time(self):
        """기상청 단기예보 발표 시각 계산 로직"""
        now = datetime.now()
        # 단기예보는 02, 05, 08, 11, 14, 17, 20, 23시 발표
        publish_times = [2, 5, 8, 11, 14, 17, 20, 23]

        # 안전하게 20분 전 시간을 기준으로 가장 가까운 발표 시각 찾기
        check_time = now - timedelta(minutes=20)
        current_hour = check_time.hour

        base_hour = max([h for h in publish_times if h <= current_hour] or [23])

        if current_hour < 2 and base_hour == 23:
            base_date = (check_time - timedelta(days=1)).strftime("%Y%m%d")
        else:
            base_date = check_time.strftime("%Y%m%d")

        return base_date, f"{base_hour:02d}00"

    def get_weather(self, nx: int, ny: int):
        base_date, base_time = self._get_base_time()

        # 사용자님이 알려주신 파라미터 형식 적용
        params = {
            'pageNo': '1',
            'numOfRows': '1000',
            'dataType': 'JSON',
            'base_date': base_date,
            'base_time': base_time,
            'nx': nx,
            'ny': ny,
            'authKey': self.auth_key  # serviceKey 대신 authKey 사용
        }

        try:
            # 기상청 허브는 파라미터를 URL 뒤에 붙이는 방식을 선호하므로 확인이 필요합니다.
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()

            # API 허브 에러 핸들링
            if 'response' not in data:
                return {"error": "Invalid API Response", "raw": data}

            items = data['response']['body']['items']['item']

            weather_data = {
                "current_temp": "--",
                "min_temp": "--",
                "max_temp": "--",
                "sky_condition": "CLEAR",
                "dust": "보통"
            }

            for item in items:
                category = item['category']
                fcst_value = item['fcstValue']

                if category == 'TMP':  # 1시간 기온
                    # 첫 번째로 나오는 TMP를 현재 기온으로 사용
                    if weather_data["current_temp"] == "--":
                        weather_data["current_temp"] = fcst_value
                elif category == 'TMN':  # 최저 기온
                    weather_data["min_temp"] = fcst_value
                elif category == 'TMX':  # 최고 기온
                    weather_data["max_temp"] = fcst_value
                elif category == 'SKY':  # 하늘 상태
                    val = int(fcst_value)
                    if val <= 1:
                        weather_data["sky_condition"] = 'CLEAR'
                    elif val <= 3:
                        weather_data["sky_condition"] = 'CLOUDY'
                    else:
                        weather_data["sky_condition"] = 'OVERCAST'

            return weather_data

        except Exception as e:
            return {"error": str(e)}