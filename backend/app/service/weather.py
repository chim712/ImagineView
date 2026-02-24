import requests
from datetime import datetime, timedelta


class WeatherService:
    def __init__(self, auth_key: str):
        self.auth_key = auth_key
        self.hub_url = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0"

        # 카테고리 코드 한글 매핑
        self.category_map = {
            'T1H': '기온(℃)', 'RN1': '1시간 강수량(mm)', 'REH': '습도(%)',
            'PTY': '강수형태', 'VEC': '풍향(deg)', 'WSD': '풍속(m/s)',
            'TMP': '1시간 기온(℃)', 'SKY': '하늘상태', 'POP': '강수확률(%)',
            'TMN': '아침 최저기온(℃)', 'TMX': '낮 최고기온(℃)', 'PCP': '1시간 강수량(문자)'
        }

        # 값 매핑
        self.pty_map = {0: '없음', 1: '비', 2: '비/눈', 3: '눈', 4: '소나기'}
        self.sky_map = {1: '맑음', 3: '구름많음', 4: '흐림'}


    def _get_ncst_time(self):
        """초단기실황용 시각 계산 (매시 40분 이전이면 전 시각 데이터 사용)"""
        now = datetime.now()
        if now.minute < 20:
            target = now - timedelta(hours=1)
        else:
            target = now
        return target.strftime("%Y%m%d"), target.strftime("%H00")

    def _get_fcst_time(self):
        """단기예보용 발표 시각 계산 (기존 로직 유지)"""
        now = datetime.now()
        publish_times = [2, 5, 8, 11, 14, 17, 20, 23]
        check_time = now - timedelta(minutes=20)
        current_hour = check_time.hour
        base_hour = max([h for h in publish_times if h <= current_hour] or [23])

        if current_hour < 2 and base_hour == 23:
            base_date = (check_time - timedelta(days=1)).strftime("%Y%m%d")
        else:
            base_date = check_time.strftime("%Y%m%d")
        return base_date, f"{base_hour:02d}00"

    # ---------------------------------------------------------
    # [1] 코어 함수: 데이터 수집 및 내부 통합 (Internal Data Fetcher)
    # ---------------------------------------------------------
    def _fetch_integrated_data(self, nx: int, ny: int):
        now = datetime.now()
        current_hour_str = now.strftime("%H00")

        result = {
            "processed": {
                "current_temp": "--", "min_temp": "--", "max_temp": "--",
                "sky_condition": "CLEAR", "dust": "보통"
            },
            "raw_ncst": [], "raw_fcst": [],
            "meta": {
                "nx": nx, "ny": ny, "fetch_time": now.strftime('%Y-%m-%d %H:%M:%S'),
                "temp_source": "NONE", "weather_source": "NONE"
            }
        }

        ncst_pty, fcst_pty, fcst_sky = 0, 0, 1

        # A. 초단기 실황 (NCST) - 온도계/센서값 우선
        n_date, n_time = self._get_ncst_time()
        try:
            res = requests.get(f"{self.hub_url}/getUltraSrtNcst",
                               params={'base_date': n_date, 'base_time': n_time, 'nx': nx, 'ny': ny,
                                       'authKey': self.auth_key, 'dataType': 'JSON'}).json()
            if 'response' in res and 'body' in res['response']:
                items = res['response']['body']['items']['item']
                result["raw_ncst"] = items
                for item in items:
                    if item['category'] == 'T1H' and item['obsrValue'] != "-999":  # 유효한 관측값일 때
                        result["processed"]["current_temp"] = item['obsrValue']
                        result["meta"]["temp_source"] = f"NCST ({n_time} 관측)"
                    if item['category'] == 'PTY':
                        ncst_pty = int(item['obsrValue'])
        except Exception as e:
            result["meta"]["ncst_error"] = str(e)

        # B. 단기 예보 (FCST) - 최저/최고 및 실황 보완용
        f_date, f_time = self._get_fcst_time()
        try:
            res = requests.get(f"{self.hub_url}/getVilageFcst",
                               params={'base_date': f_date, 'base_time': f_time, 'nx': nx, 'ny': ny,
                                       'authKey': self.auth_key, 'dataType': 'JSON', 'numOfRows': 1000}).json()
            if 'response' in res and 'body' in res['response']:
                items = res['response']['body']['items']['item']
                result["raw_fcst"] = items
                for item in items:
                    if item['category'] == 'TMN':
                        result["processed"]["min_temp"] = item['fcstValue']
                    elif item['category'] == 'TMX':
                        result["processed"]["max_temp"] = item['fcstValue']

                    if item['fcstTime'] == current_hour_str:
                        if item['category'] == 'PTY':
                            fcst_pty = int(item['fcstValue'])
                        elif item['category'] == 'SKY':
                            fcst_sky = int(item['fcstValue'])
                        # 실황 온도계가 고장나거나 데이터가 없을 때만 예보값 사용
                        if result["processed"]["current_temp"] == "--" and item['category'] == 'TMP':
                            result["processed"]["current_temp"] = item['fcstValue']
                            result["meta"]["temp_source"] = f"FCST ({f_time} 예보)"
        except Exception as e:
            result["meta"]["fcst_error"] = str(e)

        # C. 날씨 상태(배경 결정) 로직: 강수는 합집합(OR), 하늘은 예보 참조
        final_pty = ncst_pty if ncst_pty > 0 else fcst_pty
        result["meta"]["weather_source"] = "NCST" if ncst_pty > 0 else "FCST"

        if final_pty in [1, 4]:
            result["processed"]["sky_condition"] = "RAIN"
        elif final_pty in [2, 3]:
            result["processed"]["sky_condition"] = "SNOW"
        else:
            if fcst_sky >= 4:
                result["processed"]["sky_condition"] = "OVERCAST"
            elif fcst_sky >= 3:
                result["processed"]["sky_condition"] = "CLOUDY"
            else:
                result["processed"]["sky_condition"] = "CLEAR"

        return result

    # ---------------------------------------------------------
    # [2] 프론트엔드용 함수 (Data Transformer for React)
    # ---------------------------------------------------------
    def get_weather(self, nx: int, ny: int):
        data = self._fetch_integrated_data(nx, ny)
        return data["processed"]

    # ---------------------------------------------------------
    # [3] 디버그용 함수 (Human-readable Debug Formatter)
    # ---------------------------------------------------------
    def get_debug_text(self, nx: int, ny: int):
        data = self._fetch_integrated_data(nx, ny)
        current_hour = datetime.now().strftime("%H00")

        out = [f"=== Weather Debug Report ({data['meta']['fetch_time']}) ===",
               f"Location: nx={nx}, ny={ny}\n", "[1. Final Decision Summary]"]

        proc, meta = data["processed"], data["meta"]
        out.append(f" - Temperature: {proc['current_temp']}℃ (Source: {meta['temp_source']})")
        out.append(f" - Condition  : {proc['sky_condition']} (Source: {meta['weather_source']})")
        out.append(f" - Temp Range : Min {proc['min_temp']}℃ / Max {proc['max_temp']}℃\n")

        # NCST 섹션
        out.append("[2. Sensor Observation (NCST)]")
        if not data["raw_ncst"]: out.append(" - No Data Available")
        for item in data["raw_ncst"]:
            cat, val = item['category'], item['obsrValue']
            if cat == 'PTY': val = f"{val} ({self.pty_map.get(int(val), '?')})"
            out.append(f" - {self.category_map.get(cat, cat)}: {val}")

        # Timeline 섹션
        out.append("\n[3. Hourly Forecast Timeline (Next 24h)]")
        out.append(f" {'시간':<6} | {'기온':<6} | {'하늘':<8} | {'강수':<8} | {'확률'}")
        out.append("-" * 55)

        timeline = {}
        for item in data["raw_fcst"]:
            t, cat, val = item['fcstTime'], item['category'], item['fcstValue']
            if t not in timeline: timeline[t] = {"TMP": "--", "SKY": "--", "PTY": "--", "POP": "--"}
            if cat in timeline[t]: timeline[t][cat] = val

        for t in sorted(timeline.keys()):
            marker = ">" if t == current_hour else " "
            sky = self.sky_map.get(int(timeline[t]['SKY']), "?") if timeline[t]['SKY'] != "--" else "--"
            pty = self.pty_map.get(int(timeline[t]['PTY']), "?") if timeline[t]['PTY'] != "--" else "--"
            out.append(
                f"{marker} {t[:2]}:{t[2:]} | {timeline[t]['TMP']:>4}℃ | {sky:<8} | {pty:<8} | {timeline[t]['POP']}%")

        return "\n".join(out)