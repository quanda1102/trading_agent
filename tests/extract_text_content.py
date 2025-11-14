import json
import sys
from pathlib import Path
from typing import Optional


def extract_text_from_response(data: dict) -> Optional[str]:
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


def extract_all_text(jsonl_path: str, output_format: str = 'txt') -> None:
    """
    Extract all text content from a JSONL file.

    Args:
        jsonl_path: Path to the input JSONL file
        output_format: Output format - 'txt', 'json', or 'console'
    """
    results = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                text = extract_text_from_response(data)

                if text:
                    result = {
                        'custom_id': data.get('custom_id', f'line_{line_num}'),
                        'batch_id': data.get('id', ''),
                        'text': text
                    }
                    results.append(result)
                else:
                    print(f"Warning: No text found in line {line_num}", file=sys.stderr)

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error processing line {line_num}: {e}", file=sys.stderr)

    # Output based on format
    if output_format == 'console':
        output_to_console(results)
    elif output_format == 'json':
        output_to_json(results, jsonl_path)
    elif output_format == 'txt':
        output_to_text(results, jsonl_path)
    elif output_format == 'jsonl':
        output_to_jsonl(results, jsonl_path)
    else:
        print(f"Unknown format: {output_format}", file=sys.stderr)


def output_to_console(results: list):
    """Print text content to console."""
    for i, result in enumerate(results, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(results)}] Custom ID: {result['custom_id']}")
        print(f"{'='*100}")
        print(result['text'])


def output_to_text(results: list, input_path: str):
    """Save text content to separate text files."""
    input_file = Path(input_path)
    output_dir = input_file.parent / f"{input_file.stem}_text_output"
    output_dir.mkdir(exist_ok=True)

    # Also create a combined file
    combined_file = output_dir / "all_content.txt"

    with open(combined_file, 'w', encoding='utf-8') as combined:
        for result in results:
            # Individual file
            custom_id = result['custom_id'].replace('/', '_')
            individual_file = output_dir / f"{custom_id}.txt"

            with open(individual_file, 'w', encoding='utf-8') as f:
                f.write(result['text'])

            # Add to combined file
            combined.write(f"\n{'='*100}\n")
            combined.write(f"Custom ID: {result['custom_id']}\n")
            combined.write(f"Batch ID: {result['batch_id']}\n")
            combined.write(f"{'='*100}\n\n")
            combined.write(result['text'])
            combined.write("\n\n")

    print(f"\n✓ Extracted {len(results)} text contents")
    print(f"✓ Individual files saved to: {output_dir}")
    print(f"✓ Combined file: {combined_file}")


def output_to_json(results: list, input_path: str):
    """Save text content to a JSON file."""
    input_file = Path(input_path)
    output_file = input_file.parent / f"{input_file.stem}_content.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Extracted {len(results)} text contents")
    print(f"✓ Saved to: {output_file}")


def output_to_jsonl(results: list, input_path: str):
    """Save text content to a JSONL file (one JSON object per line)."""
    input_file = Path(input_path)
    output_file = input_file.parent / f"{input_file.stem}_content.jsonl"

    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"\n✓ Extracted {len(results)} text contents")
    print(f"✓ Saved to: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract text content from batch results JSONL files'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        default='/home/quan-ubuntu/Desktop/projects/trading-agent-tp/tests/backtest_results/batch_ta_results.jsonl',
        help='Path to input JSONL file (default: batch_ta_results.jsonl)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'json', 'jsonl', 'console'],
        default='txt',
        help='Output format: txt (separate files), json (single JSON), jsonl (one per line), console (print to screen)'
    )

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading from: {args.input_file}")
    print(f"Output format: {args.format}")

    extract_all_text(args.input_file, args.format)


if __name__ == "__main__":
    main()