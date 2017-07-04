echo off
for /F "tokens=* USEBACKQ" %%F IN (`type swak\version.py`) DO (
set ver=%%F
)
set version=%ver:~9,5%
echo -- Build version %version% --
set VERSION="%version%.0"
rem pyinstaller swak\win_svc.py --hidden-import=win32timezone --onefile --name swak --icon swak.ico
pyinstaller swak.spec --hidden-import=win32timezone --onefile --name swak --icon swak.ico
tools\verpatch.exe dist\swak.exe %VERSION% /va /pv %VERSION% /s description "Swak: Multi-Agent Service" /s product "Swak" /s copyright "Copyright 2017, Swak contirubutors"
set SWAK_BUILD=TRUE
coverage run --source swak --parallel-mode --module pytest tests -k test_svc
