// ImagineView.jsx
import React, { useState, useEffect } from 'react';
import './ImagineView.css';

const ImagineView = () => {
  const [time, setTime] = useState(new Date());
  const [weather, setWeather] = useState({
    current_temp: '--',
    min_temp: '--',
    max_temp: '--',
    dust: '--',
    sky_condition: 'CLEAR'
  });

  // 날씨 가져오기 함수
  const fetchWeather = async () => {
    try {
      const response = await fetch('/api/weather');
      const data = await response.json();
      if (!data.error) setWeather(data);
    } catch (error) {
      console.error("날씨 로드 실패:", error);
    }
  };

  useEffect(() => {
    fetchWeather(); // 첫 로드 시 실행

    const timer = setInterval(() => {
      const now = new Date();
      setTime(now);

      // 매 정각(0분 0초)에 날씨 정보 갱신
      if (now.getMinutes() === 0 && now.getSeconds() === 0) {
        fetchWeather();
      }
    }, 1000);return () => clearInterval(timer);
  }, []);

  /**
   * 배경 파일명을 결정하는 로직
   */
  const getBackgroundFileName = (now) => {
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const dateVal = month * 100 + day; 
    const nowMin = hour * 60 + minute;

    // TODO: 백엔드 API 연동 시 실제 weather 값을 대입 (현재는 'CLEAR' 고정)
    const weather = 'CLEAR'; 

    // 1. 10의 자리 (계절 및 날씨 코드)
    let tenDigit = 0; // 기본: 여름/맑음

    if (weather === 'SNOW') {
      tenDigit = 50;
    } else if (weather === 'RAIN') {
      tenDigit = (dateVal >= 1216 || dateVal <= 319) ? 70 : 30;
    } else if (weather === 'CLOUDY') {
      tenDigit = 10;
    } else {
      // 맑은 날 기준 특수 풍경
      if (dateVal >= 320 && dateVal <= 420) tenDigit = 20;       // 벚꽃 (3/20~4/20)
      else if (dateVal >= 1101 && dateVal <= 1215) tenDigit = 40; // 단풍 (11/1~12/15)
      else if (dateVal >= 1216 || dateVal <= 319) tenDigit = 60;  // 겨울 (12/16~3/19)
    }

    // 2. 계절별 일출(sr), 일몰(ss) 기준 시각 설정 (분 단위)
    let srMin, ssMin;
    if (month >= 3 && month <= 5) { srMin = 390; ssMin = 1110; }      // 봄 (06:30, 18:30)
    else if (month >= 6 && month <= 8) { srMin = 330; ssMin = 1200; } // 여름 (05:30, 20:00)
    else if (month >= 9 && month <= 11) { srMin = 420; ssMin = 1080; }// 가을 (07:00, 18:00)
    else { srMin = 450; ssMin = 1050; }                               // 겨울 (07:30, 17:30)

    // 3. 1의 자리 (시간 단계 코드)
    let oneDigit = 5; // 기본: 밤
    if (nowMin >= srMin && nowMin < srMin + 120) {
      oneDigit = 1; // 일출 후 2시간
    } else if (nowMin >= srMin + 120 && nowMin < ssMin - 90) {
      oneDigit = 2; // 낮 (일출 2시간 후 ~ 일몰 1.5시간 전)
    } else if (nowMin >= ssMin - 90 && nowMin < ssMin) {
      oneDigit = 3; // 일몰 전 (일몰 1.5시간 전 ~ 일몰)
    } else if (nowMin >= ssMin && nowMin < ssMin + 90) {
      oneDigit = 4; // 저녁 (일몰 ~ 일몰 1.5시간 후)
    } else {
      oneDigit = 5; // 밤 (그 외)
    }

    const finalCode = tenDigit + oneDigit;
    return `back${finalCode.toString().padStart(2, '0')}.webp`;
  };

  const bgFileName = getBackgroundFileName(time);
  const bgPath = `/assets/backgrounds/${bgFileName}`;

  // 시계 수식
  const seconds = time.getSeconds();
  const minutes = time.getMinutes();
  const hours = time.getHours();
  const secDeg = (seconds / 60) * 360;
  const minDeg = ((minutes + seconds / 60) / 60) * 360;
  const hourDeg = ((hours % 12 + minutes / 60) / 12) * 360;

  return (
    <div 
      className="dashboard-wrapper" 
      style={{ 
        backgroundImage: `url(${bgPath})`,
        transition: 'background-image 1.5s ease-in-out' // 배경 전환 효과
      }}
    >
      <div className="overlay">
        <main className="main-content">
          <section className="clock-section">
            <svg viewBox="0 0 100 100" className="analog-clock">
              <circle cx="50" cy="50" r="48" className="clock-face" />
              {/* 기존 눈금 유지 */}
              {[...Array(12)].map((_, i) => (
                <line key={i} x1="50" y1="6" x2="50" y2="12" transform={`rotate(${i * 30} 50 50)`} className="tick-mark" />
              ))}
              <line x1="50" y1="50" x2="50" y2="22" transform={`rotate(${hourDeg} 50 50)`} className="hand hour-hand" />
              <line x1="50" y1="50" x2="50" y2="12" transform={`rotate(${minDeg} 50 50)`} className="hand minute-hand" />
              <line x1="50" y1="50" x2="50" y2="18" transform={`rotate(${secDeg} 50 50)`} className="hand second-hand" />
              <circle cx="50" cy="50" r="2" className="center-dot" />
            </svg>
          </section>

          <section className="info-panel">
            <div className="card time-card">
              <p className="date-display">{time.toLocaleDateString('ko-KR')} {time.toLocaleDateString('en-US', { weekday: 'short' })}</p>
              <h1 className="digital-time">{time.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}</h1>
            </div>

            {/* 날씨 카드 부분만 교체 */}
            <div className="card weather-card updated-layout">
              <div className="weather-left">
                <div className="location-row">
                  <span className="location-pin">📍 충청남도 아산시</span> 
                </div>
                <div className="sub-info-row">
                  {/* 최저/최고 기온 및 미세먼지 */}
                  최저 {weather.min_temp}° 최고 {weather.max_temp}° · 미세먼지 {weather.dust}
                </div>
              </div>
              <div className="weather-right">
                {/* 현재 기온 강조 */}
                <span className="current-temp">{weather.current_temp}°</span>
              </div>
            </div>

            {/* 기존 주식 카드 유지 */}
            <div className="card stock-card">
              <div className="stock-item"><span>KOSPI</span> <span>7,770</span> <span className="up">▲ 500</span></div>
              <div className="stock-item"><span>KOSDAQ</span> <span>2,200</span> <span className="up">▲ 300</span></div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default ImagineView;