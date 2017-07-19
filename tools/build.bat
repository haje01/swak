echo off
for /F "tokens=* USEBACKQ" %%F IN (`type swak\version.py`) DO (
set ver=%%F
)
set version=%ver:~9,5%
echo -- Build version %version% --
set VERSION="%version%.0"
pyinstaller swak\win_svc.py --hidden-import=win32timezone --onefile --name swaksvc --icon swak.ico
rem pyinstaller swak.spec --hidden-import=win32timezone --onefile --name swaksvc --icon swak.ico
tools\verpatch.exe dist\swaksvc.exe %VERSION% /va /pv %VERSION% /s description "Swak: Multi-Agent Service" /s product "Swak" /s copyright "Copyright 2017"
set SWAK_BUILD=TRUE
coverage run --source swak --parallel-mode --module pytest tests -k test_svc
