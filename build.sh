pyinstaller swak/unix_svc.py --hidden-import=win32timezone --onefile
SWAK_BUILD=TRUE pytest --cov swak tests -k test_svc
