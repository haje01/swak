pyinstaller swak/win_svc.py --hidden-import=win32timezone --onefile --name swak --icon swak.ico --version-file version.py
rem run service test only
set SWAK_BUILD=TRUE
coverage run --source swak --parallel-mode --module pytest tests -k test_svc
