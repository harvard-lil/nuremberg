#!/bin/bash
set -euo pipefail

# if [ "${DJANGO_DEBUG:-off}" == "on" ]
# then
#     source /venv/bin/activate
#     python manage.py migrate
# fi

exec gunicorn --reload --workers=2 --threads=4 --worker-class=gthread \
     --log-file=- --bind 0.0.0.0:${PORT-8000} \
     --worker-tmp-dir=/dev/shm nuremberg.wsgi
