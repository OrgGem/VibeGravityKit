#!/usr/bin/env python3
"""
cost_estimator.py — Estimate token cost for AI coding sessions.
"""

import os
import json
import argparse
from pathlib import Path

SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.next', 'dist', 'venv', '.venv', '.agent'}
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.md', '.sql', '.sh', '.go', '.rs', '.java',
}

# Load pricing data
SCRIPT_DIR = Path(__file__).resolve().parent.parent
PRICING_FILE = SCRIPT_DIR / 'data' / 'model_pricing.json'


def count_tokens_estimate(text):
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def scan_project(path):
    """Scan project and count tokens."""
    root = Path(path)
    file_stats = []
    total_tokens = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.suffix.lower() in CODE_EXTENSIONS:
                try:
                    content = filepath.read_text(encoding='utf-8', errors='ignore')
                    tokens = count_tokens_estimate(content)
                    lines = content.count('\n') + 1
                    total_tokens += tokens
                    file_stats.append({
                        'path': str(filepath.relative_to(root)),
                        'lines': lines,
                        'tokens': tokens,
                    })
                except Exception:
                    pass

    return file_stats, total_tokens


def estimate_cost(total_tokens, model_name, pricing_data):
    """Calculate estimated cost for a session."""
    if model_name not in pricing_data['models']:
        return None

    model = pricing_data['models'][model_name]
    # Assume: input = full codebase, output = ~20% of input
    input_cost = (total_tokens / 1_000_000) * model['input_per_1m']
    output_tokens = total_tokens * 0.2
    output_cost = (output_tokens / 1_000_000) * model['output_per_1m']

    return {
        'model': model_name,
        'provider': model['provider'],
        'input_tokens': total_tokens,
        'output_tokens': int(output_tokens),
        'input_cost': round(input_cost, 4),
        'output_cost': round(output_cost, 4),
        'total_cost': round(input_cost + output_cost, 4),
        'context_window': model['context_window'],
        'fits_in_context': total_tokens <= model['context_window'],
    }


def main():
    parser = argparse.ArgumentParser(description='Estimate AI token costs for your project')
    parser.add_argument('--path', default='.', help='Project path to scan')
    parser.add_argument('--model', default='gpt-4o', help='AI model name')
    parser.add_argument('--all', action='store_true', help='Show costs for all models')
    args = parser.parse_args()

    print(f'🔍 Scanning {args.path}...\n')
    file_stats, total_tokens = scan_project(args.path)

    if not file_stats:
        print('No code files found.')
        return

    # Show top files by token count
    file_stats.sort(key=lambda x: x['tokens'], reverse=True)
    print(f'📊 Project Stats:')
    print(f'   Files: {len(file_stats)}')
    print(f'   Total Tokens: {total_tokens:,}')
    print(f'\n🔝 Top 10 largest files:')
    for f in file_stats[:10]:
        print(f"   {f['tokens']:>6,} tokens  {f['path']}")

    # Load pricing
    if PRICING_FILE.exists():
        with open(PRICING_FILE, 'r') as f:
            pricing = json.load(f)
    else:
        print('\n⚠️  Pricing data not found.')
        return

    if args.all:
        print(f'\n💰 Cost Estimates (sending full codebase):')
        print(f'{"Model":<25} {"Input $":<10} {"Output $":<10} {"Total $":<10} {"Fits?"}')
        print('-' * 65)
        for model_name in pricing['models']:
            est = estimate_cost(total_tokens, model_name, pricing)
            fits = '✅' if est['fits_in_context'] else '❌'
            print(f"{model_name:<25} ${est['input_cost']:<9.4f} ${est['output_cost']:<9.4f} ${est['total_cost']:<9.4f} {fits}")
    else:
        est = estimate_cost(total_tokens, args.model, pricing)
        if est:
            print(f'\n💰 Cost Estimate for {est["model"]} ({est["provider"]}):')
            print(f'   Input:  {est["input_tokens"]:,} tokens → ${est["input_cost"]:.4f}')
            print(f'   Output: {est["output_tokens"]:,} tokens → ${est["output_cost"]:.4f}')
            print(f'   Total:  ${est["total_cost"]:.4f} per full-context prompt')
            print(f'   Fits in context: {"✅ Yes" if est["fits_in_context"] else "❌ No (too large)"}')
        else:
            print(f'\n❌ Model "{args.model}" not found. Use --all to see all models.')

    # Optimization tips
    print(f'\n💡 Optimization Tips:')
    for tip in pricing.get('optimization_tips', [])[:3]:
        print(f"   • {tip['tip']} (saves {tip['savings']})")


if __name__ == '__main__':
    main()
