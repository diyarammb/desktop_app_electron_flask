@echo off
start cmd /k "cd frontend && npm run watch"
start cmd /k "cd backend && flask run"
exit