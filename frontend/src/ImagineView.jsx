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

  // 실제로 화면에 보여줄 배경화면 상태 (기본값 설정)
  const [activeBg, setActiveBg] = useState('back02.webp');

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
    fetchWeather();
    const timer = setInterval(() => {
      const now = new Date();
      setTime(now);
      if (now.getMinutes() === 0 && now.getSeconds() === 0) {
        fetchWeather();
      }
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  /**
   * 배경 파일명을 결정하는 로직
   */
  const getBackgroundFileName = (now, weatherStatus) => {
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const dateVal = month * 100 + day; 
    const nowMin = hour * 60 + minute;

    let tenDigit = 0; 
    if (weatherStatus === 'RAIN' || weatherStatus === 'SNOW' || weatherStatus === 'CLOUDY' || weatherStatus === 'OVERCAST') {
      if (weatherStatus === 'SNOW') tenDigit = 50;
      else if (weatherStatus === 'RAIN') tenDigit = (dateVal >= 1216 || dateVal <= 319) ? 70 : 30;
      else tenDigit = 30; 
    } else {
      if (dateVal >= 320 && dateVal <= 420) tenDigit = 20; 
      else if (dateVal >= 1101 && dateVal <= 1215) tenDigit = 40; 
      else if (dateVal >= 1216 || dateVal <= 319) tenDigit = 60; 
      else tenDigit = 0; 
    }

    let srMin, ssMin;
    if (month >= 3 && month <= 5) { srMin = 390; ssMin = 1110; }
    else if (month >= 6 && month <= 8) { srMin = 330; ssMin = 1200; }
    else if (month >= 9 && month <= 11) { srMin = 420; ssMin = 1080; }
    else { srMin = 450; ssMin = 1050; }

    let oneDigit = 5; 
    if (nowMin >= srMin && nowMin < srMin + 120) oneDigit = 1;
    else if (nowMin >= srMin + 120 && nowMin < ssMin - 90) oneDigit = 2;
    else if (nowMin >= ssMin - 90 && nowMin < ssMin) oneDigit = 3;
    else if (nowMin >= ssMin && nowMin < ssMin + 90) oneDigit = 4;
    else oneDigit = 5;

    const finalCode = tenDigit + oneDigit;
    return `back${finalCode.toString().padStart(2, '0')}.webp`;
  };

  // 배경화면 체크 및 폴백 로직 통합
  useEffect(() => {
    const targetBg = getBackgroundFileName(time, weather.sky_condition);
    const img = new Image();
    img.src = `/assets/backgrounds/${targetBg}`;

    img.onload = () => setActiveBg(targetBg);
    img.onerror = () => {
      // backXX.webp 에서 마지막 숫자인 'X'를 추출 (인덱스 5)
      const timePhase = targetBg.charAt(5); 
      const fallbackBg = `back0${timePhase}.webp`;
      setActiveBg(fallbackBg);
    };
  }, [time.getMinutes(), weather.sky_condition]);

  // 최종 경로는 activeBg를 사용합니다.
  const bgPath = `/assets/backgrounds/${activeBg}`;

  // 시계 수식
  const seconds = time.getSeconds();
  const minutes = time.getMinutes();
  const hours = time.getHours();
  const secDeg = (seconds / 60) * 360;
  const minDeg = ((minutes + seconds / 60) / 60) * 360;
  const hourDeg = ((hours % 12 + minutes / 60) / 12) * 360;

  const conditionMap = {
    'CLEAR': '맑음', 'CLOUDY': '구름많음', 'OVERCAST': '흐림',
    'RAIN': '비', 'SNOW': '눈', 'SLEET': '비/눈'
  };

  return (
    <div 
      className="dashboard-wrapper" 
      style={{ 
        backgroundImage: `url("${bgPath}")`, // 큰따옴표 추가로 안정성 확보
        transition: 'background-image 1.5s ease-in-out'
      }}
    >
      <div className="overlay">
        <main className="main-content">
          {/* 시계 섹션 */}
          <section className="clock-section">
            <svg viewBox="0 0 100 100" className="analog-clock">
              <circle cx="50" cy="50" r="48" className="clock-face" />
              {[...Array(12)].map((_, i) => (
                <line key={i} x1="50" y1="5" x2="50" y2="8" transform={`rotate(${i * 30} 50 50)`} className="tick-mark" />
              ))}
              <line x1="50" y1="50" x2="50" y2="22" transform={`rotate(${hourDeg} 50 50)`} className="hand hour-hand" />
              <line x1="50" y1="50" x2="50" y2="12" transform={`rotate(${minDeg} 50 50)`} className="hand minute-hand" />
              <line x1="50" y1="50" x2="50" y2="18" transform={`rotate(${secDeg} 50 50)`} className="hand second-hand" />
              <circle cx="50" cy="50" r="2" className="center-dot" />
            </svg>
          </section>

          {/* 정보 패널 */}
          <section className="info-panel">
            <div className="card time-card">
              <p className="date-display">{time.toLocaleDateString('ko-KR')} {time.toLocaleDateString('en-US', { weekday: 'short' })}</p>
              <h1 className="digital-time">{time.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}</h1>
            </div>

            <div className="card weather-card updated-layout">
              <div className="weather-left">
                <div className="location-row">
                  <span className="location-pin">📍 충청남도 아산시</span>
                </div>
                <div className="sub-info-row">
                  {Math.round(Number(weather.min_temp)) || 0}°c ~ {Math.round(Number(weather.max_temp)) || 0}°c  ·  미세먼지 {weather.dust}
                </div>
              </div>
              <div className="weather-right">
                <span className="condition-text">{conditionMap[weather.sky_condition] || '맑음'}</span>
                <span className="current-temp">{Math.round(Number(weather.current_temp)) || 0} °c</span>
              </div>
            </div>

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