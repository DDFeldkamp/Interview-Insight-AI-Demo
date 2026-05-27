$ErrorActionPreference = "Stop"
python tasks.py demo
Get-Content outputs/demo_report.md -TotalCount 80
