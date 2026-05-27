# Installation Guide

This repo keeps the default install small because the reviewer should be able to run the demo quickly.

## Recommended Python version

Use Python 3.11 if you can. The project supports Python `>=3.9,<3.13`, so Windows Store Python 3.9 also works.

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```


## Windows / PowerShell: no `make` required

Windows usually does not include GNU Make. Use the included Python task runner instead:

```powershell
python tasks.py demo
python tasks.py test
python tasks.py eval
python tasks.py serve
```

Or run the batch files:

```powershell
scripts\demo.bat
scripts\test.bat
scripts\eval.bat
```

If you want to use the PowerShell scripts directly and execution policy blocks them, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\demo.ps1
```

## Fastest install: CLI demo only

```bash
pip install -e .
python tasks.py demo
Get-Content outputs/demo_report.md  # Windows PowerShell
# macOS/Linux: cat outputs/demo_report.md
```

This only installs:

```text
pydantic==2.8.2
python-dotenv==1.0.1
```

## Tests and linting

```bash
python tasks.py install-dev
python tasks.py test
```

Adds:

```text
pytest==8.3.2
ruff==0.6.3
```

## Web app

```bash
python tasks.py install-api
python tasks.py serve
```

Adds:

```text
fastapi==0.112.2
uvicorn==0.30.6
python-multipart==0.0.9
```

## OpenAI structured synthesis

```bash
$env:OPENAI_API_KEY="your_key_here"  # Windows PowerShell
python tasks.py install-llm
python tasks.py openai-demo
```

Adds:

```text
openai==1.43.0
```

## Everything

```bash
python tasks.py install-all
```

Use this only if you want all optional paths in one environment. For the application reviewer, the fast CLI demo is enough to verify the core pipeline.

## Why dependencies are pinned

The previous broad ranges, such as `fastapi>=0.111` and `mypy>=1.10`, could make pip spend extra time resolving compatible transitive versions. Exact pins make the install more deterministic and faster.
