pyinstaller swak/win_svc.py --hidden-import=win32timezone --onefile
set SWAK_BUILD=TRUE
pytest --cov swak tests -k test_svc
