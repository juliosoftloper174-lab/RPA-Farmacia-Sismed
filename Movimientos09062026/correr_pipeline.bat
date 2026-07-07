@echo off
title Pipeline 09/06/2026 - Ingreso + Distribucion
cd /d "%~dp0.."
echo ==========================================
echo  Pipeline: Ingreso Central + Distribucion
echo  Fecha: 09/06/2026
echo ==========================================
.\.venv\Scripts\python.exe -m Movimientos09062026.main
pause
