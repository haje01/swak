set VERSION=0.1.0.0
pyinstaller swak\win_svc.py --hidden-import=win32timezone --onefile --name swak --icon swak.ico
tools\verpatch.exe dist\swak.exe %VERSION% /va /pv %VERSION% /s description "Swak: Multi-Agent Service" /s product "Swak" /s copyright "Copyright 2017, Swak contirubutors"
set SWAK_BUILD=TRUE
coverage run --source swak --parallel-mode --module pytest tests -k test_svc
