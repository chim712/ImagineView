# app/service/stock.py
import yfinance as yf
from datetime import datetime


class StockService:
    def get_stock_data(self):
        # KOSPI(^KS11)와 NASDAQ(^IXIC) 심볼 사용
        tickers = {"KOSPI": "^KS11", "NASDAQ": "^IXIC"}
        results = {}

        for name, symbol in tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                # fast_info나 history를 통해 최신가와 전일 종가 가져오기
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price

                    results[name] = {
                        "price": f"{current_price:,.2f}",
                        "change": f"{change:+.2f}",
                        "is_up": bool(change > 0)
                    }
                else:
                    results[name] = {"price": "--", "change": "0", "is_up": True}
            except Exception as e:
                print(f"Stock Error ({name}): {e}")
                results[name] = {"price": "Error", "change": "0", "is_up": True}

        return results