import pandas as pd
from ast import Await
from agents import Agent, Runner, function_tool, CodeInterpreterTool, WebSearchTool
from dotenv import load_dotenv
import os
from typing import List, Union
import mysql.connector
import json

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

@function_tool
def get_latest_price(
    coin_symbol: Union[List[str], str],
    time_horizons: Union[List[str], str]
) -> str:
    """
    Get the latest price data for one or more cryptocurrencies over specified time horizons.
    Return string (JSON) for model consumption.
    """
    if isinstance(coin_symbol, str):
        coin_symbol = [coin_symbol]
    if isinstance(time_horizons, str):
        time_horizons = [time_horizons]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    results = {}

    def run_query(query, params=None):
        cursor.execute(query, params or ())
        return cursor.fetchall()

    for sym in coin_symbol:
        for horizon in time_horizons:
            if horizon == "short":
                queries = [
                    """
                    SELECT * FROM finance_services.crypto_kline_hours
                    WHERE `interval` IN ('1h', '4h')
                      AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                      AND symbol = %s
                    """,
                    """
                    SELECT * FROM finance_services.futures_funding_rates
                    WHERE symbol = %s
                      AND DATE(funding_time) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """,
                    """
                    SELECT * FROM finance_services.futures_open_interests
                    WHERE symbol = %s
                      AND DATE(timestamp) >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """
                ]
            elif horizon == "medium":
                queries = ["""
                    SELECT * FROM finance_services.crypto_kline_days
                    WHERE `interval` = '1d'
                      AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                      AND symbol = %s
                """]
            elif horizon == "long":
                queries = ["""
                    SELECT * FROM finance_services.crypto_kline_weeks
                    WHERE `interval` = '1w'
                      AND DATE(open_time) >= DATE_SUB(NOW(), INTERVAL 5 YEAR)
                      AND symbol = %s
                """]
            else:
                raise ValueError(f"Invalid time horizon: {horizon}")

            all_dataframes = []
            for q in queries:
                data = run_query(q, (sym,))
                if data:
                    df = pd.DataFrame(data)
                    all_dataframes.append(df)
                else:
                    all_dataframes.append(pd.DataFrame())

            results[f"{sym}_{horizon}"] = {
                "raw_data": [df.to_dict(orient="records") for df in all_dataframes],
                "summary": [
                    {
                        "rows": len(df),
                        "columns": list(df.columns) if not df.empty else [],
                        "start_time": df["open_time"].min() if "open_time" in df else None,
                        "end_time": df["open_time"].max() if "open_time" in df else None
                    }
                    for df in all_dataframes
                ]
            }

    cursor.close()
    conn.close()
    
    return json.dumps(results, default=str)

# --- Define simple agent ---
simple_agent = Agent(
    name="SimpleAgent",
    model="gpt-5-mini",
    instructions="""Bạn là chuyên gia phân tích kỹ thuật crypto chuyên sâu, sử dụng logic phân tích đa khung thời gian (4H – 1D – 1W) kết hợp dữ liệu thực tế gồm:
- Khung giờ mà bạn sẽ được cung cấp cũng như sử dụng là giờ Việt Nam, asia, UTC+7
- Giá hiện tại, giá mở cửa, biên độ dao động 24h.
- Các mức hỗ trợ, kháng cự.
- Volume, OI, Funding rate.
- Biểu đồ giá hoặc dữ liệu nến theo ngày/giờ/tháng.

Tools: get_latest_price
- Description: Get the latest price data for one or more cryptocurrencies over specified time horizons.
- Parameters:
  - coin_symbol: The symbol of the cryptocurrency to get the latest price data for. arguments: btc, eth, sol, bnb, xrp, ada, doge, avax, link, dot.
  - time_horizons: The time horizons to get the latest price data for. Arguments: short, medium, long.

{
  "coin_symbol": "BTC",
  "time_horizons": "short",
}
Khi người dùng cung cấp dữ liệu (theo ngày, giờ, tháng hoặc biểu đồ), bạn phải xuất ra báo cáo **theo format sau:**

---

## 🕓 1. Phân tích khung 4H (Ngắn hạn – chiến thuật)
### 🔸 Diễn biến giá:
Tóm tắt biến động 4H gần nhất (giá hiện tại, biên độ, tín hiệu nến, hướng xu hướng, volume).

### 🔸 Hỗ trợ – Kháng cự ngắn hạn:
Liệt kê 2 mức hỗ trợ, 2 mức kháng cự rõ ràng.

### 🔸 Nhận định xác suất: (Trong khung thời gian dự kiến cụ thể)
- ✅ Xác suất tăng/hồi kỹ thuật (%) Trong (khung thời gian dự kiến cụ thể)
- ❌ Xác suất giảm/thủng hỗ trợ (%) Trong (khung thời gian dự kiến cụ thể)
Phân tích điều kiện volume mạnh/yếu.

### 📌 Gợi ý điểm vào – ra:
- Long: vùng giá, TP, SL  
- Short: vùng giá, TP, SL

---

## 📅 2. Phân tích khung 1D (Trung hạn – xu hướng)
Tóm tắt nến daily, xu hướng trung hạn, hỗ trợ/kháng cự chính, xác suất hồi hay retest đáy.
Gợi ý điểm vào/ra trung hạn tương tự.
Kịch bản cần nêu rõ khung thời gian dự kiến cụ thể
---

## 🪙 3. Phân tích khung 1W (Dài hạn – chiến lược)
Mô tả hành vi nến tuần, xu hướng tổng thể, hỗ trợ/kháng cự dài hạn.
Đưa ra kịch bản chính/phụ, xác suất đảo chiều.
Kịch bản cần nêu rõ khung thời gian dự kiến cụ thể
---

## 📊 Tổng hợp chiến lược
Bảng 5 cột gồm:
| Khung | Hỗ trợ | Kháng cự | Xu hướng | Kịch bản chính | Kịch bản phụ |

---

## 🧭 Gợi ý hành động
Tóm tắt hành động phù hợp cho:
- Trader ngắn hạn  
- Trader trung hạn  
- Holder dài hạn  

---

Khi có dữ liệu OI, Funding Rate, Volume:
- Tự động thêm phần nhận định “volume xác nhận / volume yếu”.
- Tự động thêm “OI tăng – gom hàng” hoặc “Funding cao – trap tăng”.
- Viết giọng chuyên nghiệp, trung lập, nhưng có tính chiến thuật và xác suất rõ ràng.

Luôn kết thúc bằng:  
👉 *Gợi ý thêm: theo dõi volume & funding ở vùng kháng cự chính để xác định breakout thật hay trap.*

---

### 📌 Yêu cầu đầu vào:
Người dùng có thể nhập:
- Dữ liệu giá (open, close, high, low, volume, funding, OI)
- Ảnh biểu đồ  
- Ngày giờ cụ thể (ví dụ: “Phân tích BTC ngày 24/10/2025 khung 4H/1D/1W”)

---

""",
    tools=[
        get_latest_price,
        CodeInterpreterTool(
            tool_config={
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }
        ),
        WebSearchTool()
    ]
)

# --- Interactive CLI ---
if __name__ == "__main__":
    import asyncio
    runner = Runner()
    async def main():
        while True:
            user_input = input("Enter your query: ").strip()
            if not user_input:
                break
            result = await runner.run(simple_agent, user_input)
            print(result.final_output)
    asyncio.run(main())
