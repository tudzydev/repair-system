#!/bin/zsh
set -eu
cd "$(dirname "$0")"

if [[ -x /opt/homebrew/bin/python3 ]]; then
  repair_python=/opt/homebrew/bin/python3
else
  repair_python=python3
fi
"$repair_python" -c 'import sys; sys.exit("Python 3.10 or newer is required") if sys.version_info < (3, 10) else None'

if [[ ! -x .venv-app/bin/python ]]; then
  "$repair_python" -m venv .venv-app
fi
if ! .venv-app/bin/python -c 'import flask, flask_sqlalchemy, flask_login, flask_wtf, PIL' >/dev/null 2>&1; then
  .venv-app/bin/python -m pip install -r requirements.txt
fi
.venv-app/bin/python -m flask --app app:create_app init-db
print '\nเปิด http://127.0.0.1:5001/login เพื่อเข้าสู่ระบบ'
print 'บัญชีฝึก: teacher / admin / technician  รหัสผ่าน: Practice123!'
print 'กด Ctrl+C เพื่อหยุดระบบ\n'
exec .venv-app/bin/python -m flask --app app:create_app run --host 127.0.0.1 --port 5001
