@echo off
REM Upload CSV to Flask
curl -X POST http://127.0.0.1:5000/upload -F "file=@test.csv"

REM Wait for 1 second
timeout /t 1 >nul

REM Fetch transactions for user
curl http://127.0.0.1:5000/transactions/default_user

pause