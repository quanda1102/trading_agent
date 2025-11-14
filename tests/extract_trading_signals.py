import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def extract_trading_signals(jsonl_path: str) -> List[Dict]:
    """
    Extract entry, stop loss, and take profit values from technical analysis results.

    Args:
        jsonl_path: Path to the JSONL file containing batch TA results

    Returns:
        List of dictionaries containing extracted trading signals
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

                # Extract trading signals
                signals = parse_trading_signals(text)
                signals['custom_id'] = data.get('custom_id', f'line_{line_num}')
                signals['batch_id'] = data.get('id', '')

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


def parse_trading_signals(text: str) -> Dict:
    """
    Parse trading signals (entry, SL, TP) from Vietnamese technical analysis text.

    Returns a dictionary with Long and Short setup information.
    """
    signals = {
        'long_setup': {},
        'short_setup': {},
        'support_levels': [],
        'resistance_levels': []
    }

    # Extract support and resistance levels
    signals['support_levels'] = extract_levels(text, r'Hỗ trợ.*?(\d[\d,]+(?:–\d[\d,]+)?)')
    signals['resistance_levels'] = extract_levels(text, r'Kháng cự.*?(\d[\d,]+(?:–\d[\d,]+)?)')

    # Find Long Setup section
    long_section = extract_section(text, 'Long Setup:')
    if long_section:
        signals['long_setup'] = parse_setup(long_section, 'long')

    # Find Short Setup section
    short_section = extract_section(text, 'Short Setup:')
    if short_section:
        signals['short_setup'] = parse_setup(short_section, 'short')

    return signals


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
        'stop_loss': None,
        'tp1': None,
        'tp2': None
    }

    # Extract Entry
    entry_match = re.search(r'Entry:.*?(\d[\d,]+(?:–\d[\d,]+)?)', section)
    if entry_match:
        setup['entry'] = clean_number(entry_match.group(1))

    # Extract Stop Loss - look for final calculated value
    sl_patterns = [
        r'Stop Loss:.*?=\s*(\d[\d,]+)',  # After = sign
        r'SL\s*≈\s*(\d[\d,]+)',  # After ≈ sign
        r'SL.*?\)\s*→\s*SL\s*≈\s*(\d[\d,]+)',  # Final SL value
    ]
    for pattern in sl_patterns:
        sl_match = re.search(pattern, section)
        if sl_match:
            setup['stop_loss'] = clean_number(sl_match.group(1))
            break

    # Extract TP1
    tp1_match = re.search(r'TP1.*?:\s*(\d[\d,]+(?:–\d[\d,]+)?)', section)
    if tp1_match:
        setup['tp1'] = clean_number(tp1_match.group(1))

    # Extract TP2
    tp2_match = re.search(r'TP2.*?:\s*(\d[\d,]+(?:–\d[\d,]+)?)', section)
    if tp2_match:
        setup['tp2'] = clean_number(tp2_match.group(1))

    return setup


def extract_levels(text: str, pattern: str) -> List[str]:
    """Extract support/resistance levels using a regex pattern."""
    matches = re.findall(pattern, text)
    return [clean_number(m) for m in matches]


def clean_number(num_str: str) -> str:
    """Clean and standardize number strings (remove commas, keep ranges)."""
    # Remove commas used as thousands separators
    num_str = num_str.replace(',', '')
    return num_str


def print_signals(signals_list: List[Dict]):
    """Print extracted signals in a readable format."""
    for signals in signals_list:
        print(f"\n{'='*80}")
        print(f"Custom ID: {signals['custom_id']}")
        print(f"Batch ID: {signals['batch_id']}")
        print(f"{'-'*80}")

        # Long Setup
        long = signals['long_setup']
        if long and any(long.values()):
            print("\nLONG SETUP:")
            print(f"  Entry:      {long.get('entry', 'N/A')}")
            print(f"  Stop Loss:  {long.get('stop_loss', 'N/A')}")
            print(f"  TP1:        {long.get('tp1', 'N/A')}")
            print(f"  TP2:        {long.get('tp2', 'N/A')}")

        # Short Setup
        short = signals['short_setup']
        if short and any(short.values()):
            print("\nSHORT SETUP:")
            print(f"  Entry:      {short.get('entry', 'N/A')}")
            print(f"  Stop Loss:  {short.get('stop_loss', 'N/A')}")
            print(f"  TP1:        {short.get('tp1', 'N/A')}")
            print(f"  TP2:        {short.get('tp2', 'N/A')}")

        # Support/Resistance
        if signals['support_levels']:
            print(f"\nSupport Levels: {', '.join(signals['support_levels'])}")
        if signals['resistance_levels']:
            print(f"Resistance Levels: {', '.join(signals['resistance_levels'])}")


def save_to_json(signals_list: List[Dict], output_path: str):
    """Save extracted signals to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(signals_list, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def main():
    # Input and output paths
    input_file = "/home/quan-ubuntu/Desktop/projects/trading-agent-tp/tests/backtest_eth_oct/batch_ta_results.jsonl"
    output_file = "/home/quan-ubuntu/Desktop/projects/trading-agent-tp/tests/backtest_eth_oct/extracted_signals.json"

    print(f"Reading from: {input_file}")

    # Extract signals
    signals = extract_trading_signals(input_file)

    print(f"\nExtracted {len(signals)} trading signal(s)")

    # Print results
    print_signals(signals)

    # Save to JSON
    save_to_json(signals, output_file)


if __name__ == "__main__":
    main()
