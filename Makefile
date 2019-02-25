USER=***REMOVED***
SERVER=***REMOVED***
HTTP_PORT=5001
SSH_PORT=22

.PHONY: install fetcher server rename sync 

install:
	pip3 install -r requirements.txt

fetcher:
	until python3 fetcher.py; do echo "Fetcher crashed with exit code $?.  Respawning.." >&2; sleep 1; done

server:
	python3 update_names.py
	gunicorn -w 2 --log-level debug --bind 0.0.0.0:${HTTP_PORT} wsgi

sync:
	rsync --delete --exclude='.ipynb_checkpoints' --exclude='.git' --exclude='log' --exclude='log_backup' --exclude='generated_graphs' --exclude='fetcher_log.txt' --exclude='__pycache__' --exclude='.vscode' --exclude='.DS_Store' --rsh="ssh -p ${SSH_PORT}" -aruzhv . ${USER}@${SERVER}:~/zzzzz

backup:
	rsync --rsh="ssh -p ${SSH_PORT}" -aruzhv ${USER}@${SERVER}:~/zzzzz/log .
