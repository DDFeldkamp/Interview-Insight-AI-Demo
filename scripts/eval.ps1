$ErrorActionPreference = "Stop"
python tasks.py eval
Get-Content outputs/eval_results.json -TotalCount 120
