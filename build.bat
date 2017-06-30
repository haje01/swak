pyinstaller swak/win_svc.py --hidden-import=win32timezone --onefile
rem run service test only
set SWAK_BUILD=TRUE
coverage run --source swak -m pytest tests -k test_svc
