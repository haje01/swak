pyinstaller swak/unix_svc.py --hidden-import=win32timezone --onefile --name swakd --icon swak.ico
# export SWAK_BUILD=TRUE
# coverage run --source swak --parallel-mode --module pytest tests -k test_svc
