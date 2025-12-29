from datetime import datetime
import pytz
import yfinance as yf

def get_current_time(timezone: str = "Asia/Seoul"):
  tz = pytz.timezone(timezone)
  now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
  now_timezone = f'{now} {timezone}'
  print(now_timezone)
  return now_timezone

def get_yf_stock_info(ticker: str):
  stock = yf.Ticker(ticker)
  info = stock.info
  print(info)
  return str(info)

def get_yf_stock_history(ticker: str, period: str = "5d"):
  stock = yf.Ticker(ticker)
  history = stock.history(period=period)
  history_md = history.to_markdown()
  print(history_md)
  return history_md

def get_yf_stock_recommendations(ticker: str):
  stock = yf.Ticker(ticker)
  recommendations = stock.recommendations
  recommendations_md = recommendations.to_markdown()
  print(recommendations_md)
  return recommendations_md

tools = [
  {
    "type": "function",
    "function": {
      "name": "get_current_time",
      "description": "현재 날짜와 시간을 반환 합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "timezone": {
            "type": "string",
            "description": "현재 날자와 시간을 반환할 타임존을 입력하세요.",
          }
        },
        "required": ["timezone"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_yf_stock_info",
      "description": "주식 정보를 반환 합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "ticker": {
            "type": "string",
            "description": "주식 종목 코드를 입력하세요.",
          }
        },
        "required": ["ticker"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_yf_stock_history",
      "description": "주가 정보 데이터를 반환 합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "ticker": {
            "type": "string",
            "description": "주식 종목 코드를 입력하세요.",
          },
          "period": {
            "type": "string",
            "description": "주식 데이터를 반환할 기간을 입력하세요.",
          }
        },
        "required": ["ticker", "period"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_yf_stock_recommendations",
      "description": "주식 추천 정보를 반환 합니다.",
      "parameters": {
        "type": "object", 
        "properties": {
          "ticker": {
            "type": "string",
            "description": "주식 종목 코드를 입력하세요.",
          }
        },
        "required": ["ticker"]
      }
    }
  },
]

if __name__ == "__main__":
  # get_current_time('America/New_York')
  # info = get_yf_stock_info("MSFT")
  history = get_yf_stock_history("MSFT")
  recommendations = get_yf_stock_recommendations("MSFT")
