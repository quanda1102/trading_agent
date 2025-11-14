import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def extract_trading_signals_enhanced(jsonl_path: str) -> List[Dict]:
    """
    Extract entry, stop loss, take profit values and time range information
    from technical analysis results.

    Args:
        jsonl_path: Path to the JSONL file containing batch TA results

    Returns:
        List of dictionaries containing extracted trading signals with time info
    """
    results = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                # Extract the analysis text from the response
                text = extract_text_from_response(data)
                if not text:
                    print(f"Warning: No text found in line {line_num}")
                    continue

                # Extract all information
                signals = parse_enhanced_signals(text)
                signals['custom_id'] = data.get('custom_id', f'line_{line_num}')
                signals['batch_id'] = data.get('id', '')
                signals['created_at'] = data.get('response', {}).get('body', {}).get('created_at', None)

                results.append(signals)

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}")
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")

    return results


def extract_text_from_response(data: Dict) -> Optional[str]:
    """Extract the text content from the response structure."""
    try:
        output = data['response']['body']['output']
        for item in output:
            if item.get('type') == 'message':
                content = item.get('content', [])
                for c in content:
                    if c.get('type') == 'output_text':
                        return c.get('text', '')
    except (KeyError, TypeError):
        pass
    return None


def parse_enhanced_signals(text: str) -> Dict:
    """
    Parse trading signals and time range information from Vietnamese technical analysis text.

    Returns a dictionary with time info, OHLCV, Long/Short setup information.
    """
    signals = {
        'time_info': {},
        'ohlcv': {},
        'market_context': {},
        'long_setup': {},
        'short_setup': {},
        'support_levels': [],
        'resistance_levels': [],
        'probability_scenarios': []
    }

    # Extract time information
    signals['time_info'] = extract_time_info(text)

    # Extract OHLCV data
    signals['ohlcv'] = extract_ohlcv(text)

    # Extract market context (24h range, volume, etc)
    signals['market_context'] = extract_market_context(text)

    # Extract support and resistance levels
    signals['support_levels'] = extract_support_levels(text)
    signals['resistance_levels'] = extract_resistance_levels(text)

    # Find Long Setup section
    long_section = extract_section(text, 'Long Setup:')
    if long_section:
        signals['long_setup'] = parse_setup(long_section, 'long')

    # Find Short Setup section
    short_section = extract_section(text, 'Short Setup:')
    if short_section:
        signals['short_setup'] = parse_setup(short_section, 'short')

    # Extract probability scenarios
    signals['probability_scenarios'] = extract_probability_scenarios(text)

    return signals


def extract_time_info(text: str) -> Dict:
    """Extract time range and analysis timestamp information."""
    time_info = {
        'candle_time': None,
        'candle_time_vn': None,
        'report_time_vn': None,
        'data_range': None
    }

    # Extract candle time
    # Pattern: "Nến cuối (2025-05-19 23:00)"
    candle_match = re.search(r'Nến cuối \((\d{4}-\d{2}-\d{2} \d{2}:\d{2})\)', text)
    if candle_match:
        time_info['candle_time'] = candle_match.group(1)

    # Extract report time VN
    # Pattern: "Thời điểm báo cáo (candle cuối): 2025-10-08 06:00 VN"
    report_match = re.search(r'Thời điểm báo cáo.*?:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*VN', text)
    if report_match:
        time_info['report_time_vn'] = report_match.group(1)

    # Extract data range
    # Pattern: "(khoảng 2025-10-01 → 2025-10-07)"
    range_match = re.search(r'\(khoảng (\d{4}-\d{2}-\d{2})\s*→\s*(\d{4}-\d{2}-\d{2})\)', text)
    if range_match:
        time_info['data_range'] = {
            'start': range_match.group(1),
            'end': range_match.group(2)
        }

    return time_info


def extract_ohlcv(text: str) -> Dict:
    """Extract OHLCV data from the summary section."""
    ohlcv = {
        'open': None,
        'high': None,
        'low': None,
        'close': None,
        'volume': None
    }

    # Pattern: "O=2417.58, H=2473.70, L=2383.80, C=2466.63, V=153,649.80"
    ohlcv_match = re.search(
        r'O=([\d,]+\.?\d*),?\s*H=([\d,]+\.?\d*),?\s*L=([\d,]+\.?\d*),?\s*C=([\d,]+\.?\d*),?\s*V=([\d,]+\.?\d*)',
        text
    )

    if ohlcv_match:
        ohlcv['open'] = clean_number(ohlcv_match.group(1))
        ohlcv['high'] = clean_number(ohlcv_match.group(2))
        ohlcv['low'] = clean_number(ohlcv_match.group(3))
        ohlcv['close'] = clean_number(ohlcv_match.group(4))
        ohlcv['volume'] = clean_number(ohlcv_match.group(5))

    return ohlcv


def extract_market_context(text: str) -> Dict:
    """Extract market context like current price, 24h range, volume analysis."""
    context = {
        'current_price': None,
        '24h_high': None,
        '24h_low': None,
        '24h_change_pct': None,
        'volume_vs_avg': None,
        'avg_volume_20': None
    }

    # Current price
    price_match = re.search(r'Giá hiện tại:\s*([\d,]+\.?\d*)\s*USD', text)
    if price_match:
        context['current_price'] = clean_number(price_match.group(1))

    # 24h High
    high_match = re.search(r'High\s*[=:]\s*([\d,]+\.?\d*)', text)
    if high_match:
        context['24h_high'] = clean_number(high_match.group(1))

    # 24h Low
    low_match = re.search(r'Low\s*[=:]\s*([\d,]+\.?\d*)', text)
    if low_match:
        context['24h_low'] = clean_number(low_match.group(1))

    # 24h change percentage
    change_match = re.search(r'thay đổi 24h.*?([−-]?\d+\.?\d*)%', text)
    if change_match:
        context['24h_change_pct'] = change_match.group(1).replace('−', '-')

    # Volume vs average
    vol_avg_match = re.search(r'Volume.*?trung bình.*?[=:]\s*([\d,]+\.?\d*)', text)
    if vol_avg_match:
        context['avg_volume_20'] = clean_number(vol_avg_match.group(1))

    vol_pct_match = re.search(r'volume.*?(\d+\.?\d*)%.*?avg20', text, re.IGNORECASE)
    if vol_pct_match:
        context['volume_vs_avg'] = vol_pct_match.group(1) + '%'

    return context


def extract_support_levels(text: str) -> List[Dict]:
    """Extract support levels with their ranges."""
    supports = []

    # Pattern: "Hỗ trợ 1: 2,400 USD | (vùng 2,388 – 2,412)"
    pattern = r'Hỗ trợ\s*(\d+):\s*([\d,]+(?:–[\d,]+)?)\s*(?:USD)?(?:\s*\|\s*\(vùng\s*([\d,]+(?:\s*[–-]\s*[\d,]+)?)\))?'
    matches = re.findall(pattern, text)

    for match in matches:
        level_num = match[0]
        price = clean_number(match[1])
        zone = clean_number(match[2]) if match[2] else None

        supports.append({
            'level': f'Support_{level_num}',
            'price': price,
            'zone': zone
        })

    return supports


def extract_resistance_levels(text: str) -> List[Dict]:
    """Extract resistance levels with their ranges."""
    resistances = []

    # Pattern: "Kháng cự 1: 2,588 USD | (vùng 2,575 – 2,601)"
    pattern = r'Kháng cự\s*(\d+):\s*([\d,]+(?:–[\d,]+)?)\s*(?:USD)?(?:\s*\|\s*\(vùng\s*([\d,]+(?:\s*[–-]\s*[\d,]+)?)\))?'
    matches = re.findall(pattern, text)

    for match in matches:
        level_num = match[0]
        price = clean_number(match[1])
        zone = clean_number(match[2]) if match[2] else None

        resistances.append({
            'level': f'Resistance_{level_num}',
            'price': price,
            'zone': zone
        })

    return resistances


def extract_probability_scenarios(text: str) -> List[Dict]:
    """Extract probability scenarios from the analysis."""
    scenarios = []

    # Find the probability table section
    prob_section = re.search(
        r'Xác suất diễn biến.*?\n\n(.*?)(?:\n\n[4-9]\)|$)',
        text,
        re.DOTALL
    )

    if prob_section:
        section_text = prob_section.group(1)

        # Pattern: "| Tăng / hồi kỹ thuật | 50% | ..."
        pattern = r'\|\s*([^|]+?)\s*\|\s*(\d+)%\s*\|'
        matches = re.findall(pattern, section_text)

        for match in matches:
            scenario = match[0].strip()
            probability = match[1].strip()

            if scenario and scenario.lower() not in ['kịch bản', 'scenario']:
                scenarios.append({
                    'scenario': scenario,
                    'probability': probability + '%'
                })

    return scenarios


def extract_section(text: str, start_marker: str) -> Optional[str]:
    """Extract a section of text starting from a marker until the next major section."""
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return None

    # Find the end (next major section or end of relevant content)
    end_markers = ['Long Setup:', 'Short Setup:', 'Quy tắc quản trị', '5) Tổng hợp']
    end_idx = len(text)

    for marker in end_markers:
        idx = text.find(marker, start_idx + len(start_marker))
        if idx != -1 and idx < end_idx:
            end_idx = idx

    return text[start_idx:end_idx]


def parse_setup(section: str, setup_type: str) -> Dict:
    """Parse entry, SL, and TP from a setup section."""
    setup = {
        'entry': None,
        'entry_type': None,  # aggressive/conservative
        'stop_loss': None,
        'stop_loss_alt': None,  # alternative SL (if 2x ATR provided)
        'tp1': None,
        'tp2': None,
        'atr_multiplier': None
    }

    # Extract Entry with type
    entry_match = re.search(r'Entry.*?(\(.*?\))?:?\s*(?:vùng giá\s*)?([\d,]+(?:\s*[–-]\s*[\d,]+)?)\s*USD', section)
    if entry_match:
        entry_type = entry_match.group(1)
        if entry_type:
            setup['entry_type'] = entry_type.strip('()')
        setup['entry'] = clean_number(entry_match.group(2))

    # Extract Stop Loss - look for final calculated values
    sl_patterns = [
        r'Stop.*?≈\s*([\d,]+)\s*USD',  # After ≈ sign
        r'Stop.*?=\s*([\d,]+)\s*USD',  # After = sign
    ]
    sl_matches = []
    for pattern in sl_patterns:
        matches = re.findall(pattern, section)
        sl_matches.extend(matches)

    if sl_matches:
        setup['stop_loss'] = clean_number(sl_matches[0])
        if len(sl_matches) > 1:
            setup['stop_loss_alt'] = clean_number(sl_matches[-1])

    # Extract ATR multiplier
    atr_match = re.search(r'(\d+(?:\.\d+)?)\s*×\s*ATR', section)
    if atr_match:
        setup['atr_multiplier'] = atr_match.group(1)

    # Extract TP1
    tp1_match = re.search(r'TP1.*?:\s*([\d,]+(?:\s*[–-]\s*[\d,]+)?)\s*(?:USD|\()', section)
    if tp1_match:
        setup['tp1'] = clean_number(tp1_match.group(1))

    # Extract TP2
    tp2_match = re.search(r'TP2.*?:\s*([\d,]+(?:\s*[–-]\s*[\d,]+)?)\s*(?:USD|\()', section)
    if tp2_match:
        setup['tp2'] = clean_number(tp2_match.group(1))

    return setup


def clean_number(num_str: str) -> str:
    """Clean and standardize number strings (remove commas, keep ranges)."""
    if not num_str:
        return None
    # Remove commas used as thousands separators
    num_str = num_str.replace(',', '').strip()
    # Replace various dash types with standard hyphen for ranges
    num_str = re.sub(r'\s*[–—]\s*', '-', num_str)
    return num_str


def print_enhanced_signals(signals_list: List[Dict]):
    """Print extracted signals in a readable format with time info."""
    for signals in signals_list:
        print(f"\n{'='*100}")
        print(f"Custom ID: {signals['custom_id']}")
        print(f"Batch ID: {signals['batch_id']}")
        if signals.get('created_at'):
            dt = datetime.fromtimestamp(signals['created_at'])
            print(f"Created At: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*100}")

        # Time Information
        time_info = signals['time_info']
        if any(time_info.values()):
            print(f"\n{'─'*100}")
            print("TIME INFORMATION:")
            if time_info.get('candle_time'):
                print(f"  Candle Time:     {time_info['candle_time']}")
            if time_info.get('report_time_vn'):
                print(f"  Report Time VN:  {time_info['report_time_vn']}")
            if time_info.get('data_range'):
                dr = time_info['data_range']
                print(f"  Data Range:      {dr.get('start')} → {dr.get('end')}")

        # OHLCV Data
        ohlcv = signals['ohlcv']
        if any(ohlcv.values()):
            print(f"\n{'─'*100}")
            print("OHLCV DATA:")
            print(f"  Open:    {ohlcv.get('open', 'N/A')}")
            print(f"  High:    {ohlcv.get('high', 'N/A')}")
            print(f"  Low:     {ohlcv.get('low', 'N/A')}")
            print(f"  Close:   {ohlcv.get('close', 'N/A')}")
            print(f"  Volume:  {ohlcv.get('volume', 'N/A')}")

        # Market Context
        context = signals['market_context']
        if any(context.values()):
            print(f"\n{'─'*100}")
            print("MARKET CONTEXT:")
            if context.get('current_price'):
                print(f"  Current Price:    {context['current_price']} USD")
            if context.get('24h_high') or context.get('24h_low'):
                print(f"  24h Range:        {context.get('24h_high', 'N/A')} / {context.get('24h_low', 'N/A')}")
            if context.get('24h_change_pct'):
                print(f"  24h Change:       {context['24h_change_pct']}%")
            if context.get('volume_vs_avg'):
                print(f"  Volume vs Avg:    {context['volume_vs_avg']}")
            if context.get('avg_volume_20'):
                print(f"  Avg Volume (20):  {context['avg_volume_20']}")

        # Support/Resistance Levels
        if signals['support_levels']:
            print(f"\n{'─'*100}")
            print("SUPPORT LEVELS:")
            for supp in signals['support_levels']:
                zone_str = f" (Zone: {supp['zone']})" if supp.get('zone') else ""
                print(f"  {supp['level']}: {supp['price']}{zone_str}")

        if signals['resistance_levels']:
            print(f"\n{'─'*100}")
            print("RESISTANCE LEVELS:")
            for res in signals['resistance_levels']:
                zone_str = f" (Zone: {res['zone']})" if res.get('zone') else ""
                print(f"  {res['level']}: {res['price']}{zone_str}")

        # Probability Scenarios
        if signals['probability_scenarios']:
            print(f"\n{'─'*100}")
            print("PROBABILITY SCENARIOS:")
            for scenario in signals['probability_scenarios']:
                print(f"  {scenario['scenario']:<25} {scenario['probability']:>5}")

        # Long Setup
        long = signals['long_setup']
        if long and any(long.values()):
            print(f"\n{'─'*100}")
            print("LONG SETUP:")
            if long.get('entry_type'):
                print(f"  Type:       {long['entry_type']}")
            print(f"  Entry:      {long.get('entry', 'N/A')}")
            print(f"  Stop Loss:  {long.get('stop_loss', 'N/A')}", end='')
            if long.get('stop_loss_alt'):
                print(f" (Alt: {long['stop_loss_alt']})", end='')
            print()
            print(f"  TP1:        {long.get('tp1', 'N/A')}")
            print(f"  TP2:        {long.get('tp2', 'N/A')}")
            if long.get('atr_multiplier'):
                print(f"  ATR Multi:  {long['atr_multiplier']}x")

        # Short Setup
        short = signals['short_setup']
        if short and any(short.values()):
            print(f"\n{'─'*100}")
            print("SHORT SETUP:")
            if short.get('entry_type'):
                print(f"  Type:       {short['entry_type']}")
            print(f"  Entry:      {short.get('entry', 'N/A')}")
            print(f"  Stop Loss:  {short.get('stop_loss', 'N/A')}", end='')
            if short.get('stop_loss_alt'):
                print(f" (Alt: {short['stop_loss_alt']})", end='')
            print()
            print(f"  TP1:        {short.get('tp1', 'N/A')}")
            print(f"  TP2:        {short.get('tp2', 'N/A')}")
            if short.get('atr_multiplier'):
                print(f"  ATR Multi:  {short['atr_multiplier']}x")


def save_to_json(signals_list: List[Dict], output_path: str):
    """Save extracted signals to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(signals_list, f, indent=2, ensure_ascii=False)
    print(f"\n\nResults saved to: {output_path}")


def main():
    # Input and output paths
    input_file = "/home/quan-ubuntu/Desktop/projects/trading-agent-tp/tests/backtest_results/batch_ta_results.jsonl"
    output_file = "/home/quan-ubuntu/Desktop/projects/trading-agent-tp/tests/backtest_results/extracted_enhanced_signals.json"

    print(f"Reading from: {input_file}")

    # Extract signals
    signals = extract_trading_signals_enhanced(input_file)

    print(f"\nExtracted {len(signals)} trading signal(s)")

    # Print results (only first 3 for preview if many)
    if len(signals) > 3:
        print(f"\nShowing first 3 results (total: {len(signals)})...")
        print_enhanced_signals(signals[:3])
        print(f"\n... ({len(signals) - 3} more results)")
    else:
        print_enhanced_signals(signals)

    # Save to JSON
    save_to_json(signals, output_file)


if __name__ == "__main__":
    main()
