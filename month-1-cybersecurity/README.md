# Month 1: Cybersecurity — SOC Triage Agent

A production-grade LLM-powered Security Operations Center (SOC) triage agent that analyzes raw SIEM logs and outputs guaranteed structured threat reports using Pydantic schemas.

## Features
- **Dual Provider Support**: OpenAI (GPT-4o-mini, GPT-4o) & Anthropic (Claude 3 family)
- **Schema-Guaranteed Output**: Pydantic v2 validation with stateful retry loops
- **Mock Mode**: Test the entire pipeline offline without API keys
- **Golden Dataset Evaluation**: Benchmark pass/fail rates against labeled ground truth

## Quick Start

### 1. Install dependencies
```bash
cd /workspaces/fde-mastery
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp month-1-cybersecurity/.env.example /workspaces/fde-mastery/.env
# Edit .env and paste real keys
```

### 3. Run offline (no API keys needed)
```bash
cd month-1-cybersecurity
python main.py --mock
```

### 4. Run with OpenAI
```bash
export OPENAI_API_KEY="sk-..."
python main.py --provider openai --model gpt-4o-mini
```

### 5. Run with Anthropic
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py --provider anthropic --model claude-3-opus-20240229
```

> **Note**: If you get `404 Not Found` on Anthropic models, your API key may not have access to Claude 3.5. Try the fallback models listed in the error message, or use `--mock`.

## CLI Options

| Flag | Description |
|------|-------------|
| `--provider {openai,anthropic}` | LLM provider |
| `--model MODEL` | Specific model ID |
| `--mock` | Offline synthetic responses |
| `--eval-only` | Skip demo, run benchmark only |
| `--demo-only` | Skip benchmark, run demo only |

## Project Structure

```
month-1-cybersecurity/
├── __init__.py
├── schemas.py          # Pydantic models (Log, Report, Enums)
├── agent.py            # SOCTriageAgent with retry loops
├── eval_harness.py     # Golden dataset benchmark
├── main.py             # CLI entry point
├── golden_dataset.json # Labeled test cases
└── .env.example        # API key template
```

## Golden Dataset Format

Each entry in `golden_dataset.json` contains:
- `input_log`: Raw SIEM fields matching `RawSecurityLog` schema
- `expected_output`: Ground-truth labels for severity, category, and action
