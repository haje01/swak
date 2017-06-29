pyinstaller swak/unix_svc.py --hidden-import=win32timezone --onefile
pytest --cov swak tests -k test_svc
