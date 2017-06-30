pyinstaller swak/unix_svc.py --hidden-import=win32timezone --onefile
export SWAK_BUILD=TRUE
coverage run --source swak -a -m pytest tests -k test_svc
