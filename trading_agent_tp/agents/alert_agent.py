from typing import Any, Literal, Optional
from pydantic import BaseModel
import requests
from agents import Agent, Runner, function_tool

class Condition(BaseModel):
    leftType: Literal["price", "volume", "value"] = "price"
    operator: Literal["crossing_up", "crossing_down", "greater_than", "less_than"] = "crossing_up"
    rightType: Literal["price", "volume", "value"] = "value"
    rightValue: Optional[float] = 120000

class Alert(BaseModel):
    symbol: str
    interval: str
    triggerMode: Literal["only_once", "once_per_minute"] = "only_once"
    expiresAt: str = "2025-12-06T09:13:00Z"
    condition: Condition

@function_tool
def set_alert(alert: Alert) -> Any:
    """
    Send an alert message via api
    """
    response = requests.post(
        url="https://fin-services-crawler.thienphuoc.media/alerts/create",
        json=alert.model_dump()
    )
    return response.json()

agent = Agent(
    name="Alert Agent",
    model="gpt-4.1-mini",
    instructions="""
Bạn là chuyên gia tạo cảnh báo tài chính.
Nhiệm vụ của bạn: dựa trên nội dung phân tích kỹ thuật mà tôi cung cấp, hãy tạo **một** alert duy nhất phù hợp nhất 
và gọi tool `set_alert`.
**Schema mẫu:**
```
Alert(
    symbol='BTCUSDT',
    interval='1h',
    triggerMode='only_once',
    expiresAt='2025-11-15T09:13:00Z',
    condition=Condition(
        leftType='price',
        operator='greater_than',
        rightType='value',
        rightValue=90000.0
    )
)
```

**Quy tắc bắt buộc:**

1. **Mọi thông tin** như `symbol`, `interval`, `operator`, mức giá, hướng giao cắt, target, vùng quan trọng… đều phải 
được **suy luận trực tiếp từ nội dung phân tích**.
2. **Ngoại lệ duy nhất:**
* `expiresAt` **không lấy từ phân tích** mà bạn phải **tự tính bằng cách cộng thêm 48 giờ** so với **ngày phân tích** 
được nêu trong dữ liệu.
3. `expiresAt` phải đúng format ISO:
**`YYYY-MM-DDTHH:MM:SSZ`**
4. Nếu phân tích chứa nhiều tín hiệu, hãy chọn **tín hiệu quan trọng nhất** để tạo 1 alert duy nhất.
5. Nếu mức giá không ghi rõ, bạn phải **tự diễn giải kỹ thuật** (support, resistance, breakout point, trendline,
 retest…).
6. Tuyệt đối **không hỏi lại tôi**; bạn phải tự hoàn thiện toàn bộ alert từ nội dung phân tích.
7. Khi hoàn tất, hãy gọi tool `set_alert` với object Alert đúng cấu trúc.
    """,
    tools=[set_alert]
)

if __name__ == "__main__":
    runner = Runner()
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    user_input = """
🕓 1. Phân tích khung 4H (Ngắn hạn – chiến thuật)\n\n### Diễn biến giá:\n- Giá hiện tại (mốc dữ liệu gần nhất, giờ VN
 UTC+7): ~103,069 → close 4H/latest 1H cho thấy vùng giá hiện hành ~99,000–103,000 tùy candle; cập nhật gần nhất: 
 2025-11-14 09:00 (VN) — last 1H close 99,255.6, last 4H candle (07:00–11:00) đóng tại 98,973.95.  \n- Biên độ 24h tham 
 khảo (từ 2025-11-13 09:00 → 2025-11-14 09:00): High ≈ 103,780; Low ≈ 98,000.  \n- Tín hiệu nến: recent 4H shows mạnh → 
 nến giảm/ thân dài xuống (breakout xuống vùng 100k rồi test 98k).  \n- Volume: xuất hiện volume lớn trên các 4H giảm
  (ví dụ 4H có volume lớn ~2.4k–2.6k), nghĩa là bán ra với thanh khoản cao — volume xác nhận giảm.  \n- OI: open
   interest tăng đáng kể trước/đúng vùng giảm (OI từ ~87k → đỉnh ~91.6k coin trong khoảng 14/11 → 14/11 early), sau đó
    giữ cao ~90k — OI tăng đồng thời giá giảm = khả năng: gom vị thế shorts hoặc đóng long (tín hiệu thị trường có vị 
    thế mở nhiều).  \n- Funding rate: gần đây dương (ví dụ funding ≈ 8.57e-05 vào 2025-11-14 07:00) — longs đang trả phí, thị trường vẫn có bias “long-heavy” nhưng giá giảm cho thấy khả năng trap/long liquidation.\n\n### 🔸 Hỗ trợ – Kháng cự ngắn hạn:\n- Hỗ trợ (2 mức):  \n  1) 98,000 (mức low intraday & đáy 4H).  \n  2) 100,600 – 101,700 (vùng hỗ trợ tạm, nhiều nến small-body & retest).  \n- Kháng cự (2 mức):  \n  1) 103,700 – 103,900 (local high & vùng retest 4H).  \n  2) 105,000 – 106,600 (vùng cung/liquidity trên, nhiều lệnh chặn).\n\n### 🔸 Nhận định xác suất (khung 4H, trong 24–48 giờ tới):\n- ✅ Xác suất hồi/retest kháng cự 103.7k–103.9k: ~35% (cần retest có volume giảm và OI giảm kèm theo).  \n- ❌ Xác suất giảm/thủng 98k tiếp tục về ~95k: ~65% (volume lớn trên các phiên giảm + OI vẫn tăng => áp lực bán/short accumulation).  \nPhân tích điều kiện volume/OI: volume giảm mạnh trên phiên giảm được xác nhận (volume cao khi giá giảm) → xác suất tiếp tục bán cao; OI tăng đồng thời price giảm = nhiều vị thế mở (thường là shorts được mở hoặc longs bị thanh lý) — cảnh giác trap tăng.\n\n### 📌 Gợi ý điểm vào – ra (chiến thuật 4H):\n- Long (scalp/dip-buy): vào vùng 98,000 – 99,200.  \n  - TP (partial): 101,500 → 103,500.  \n  - SL: 96,800 (dưới 98k để tránh fakeout).  \n  - Rủi ro: nếu OI tiếp tục tăng và funding vẫn dương, long có thể bị squeeze → dùng tỷ lệ vốn nhỏ.  \n- Short (retest/failed-break): short khi retest thất bại tại 103,200 – 104,500 (vùng kháng cự + volume giảm trên tăng).  \n  - TP: 100,500 → 98,200.  \n  - SL: 105,500 (vượt vùng 105k/stop lớn).  \n  - Lưu ý: nếu breakout qua 106k với volume lớn và OI tiếp tục tăng → stop loss nhanh.\n\n---\n\n## 📊 Tổng hợp chiến lược (chỉ khung 4H theo yêu cầu)\n| Khung | Hỗ trợ | Kháng cự | Xu hướng | Kịch bản chính | Kịch bản phụ |\n|---|---:|---:|---|---|---|\n| 4H | 98,000 / 100,600 | 103,700 / 105,500 | Bearish ngắn hạn (giảm với volume xác nhận) | Giá tiếp tục giảm tới ~95k–96k (OI cao, volume bán lớn) — ưu tiên tìm điểm long thăm dò tại 98k | Giá hồi kỹ thuật retest 103.7k rồi fail → short theo momentum |\n\n---\n\n🧭 Gợi ý hành động (ngắn hạn, khung 4H):\n- Trader ngắn hạn: ưu tiên chờ dip vào 98k để mua nhỏ (sizing nhỏ) hoặc chờ failed-retest tại 103–104k để short. Quản trị rủi ro: SL hẹp, chia vị thế.  \n- (Không phân tích trung/dài hạn theo yêu cầu.)\n\nCác điểm cần theo dõi tức thì: movement & volume tại 98k (hỗ trợ), OI biến động lên/ xuống, funding rate duy trì dương (còn trap long).\n\n👉 *Gợi ý thêm: theo dõi volume & funding ở vùng kháng cự chính để xác định breakout thật hay trap.
created_at 2025-11-14T02:36:19.107916,
    """
    async def main():
        result = await runner.run(agent, user_input)
        print(result.final_output)
    asyncio.run(main())