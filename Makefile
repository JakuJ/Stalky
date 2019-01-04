.PHONY: install server rename sync 

install:
	pip3 install -r dependencies.txt

server:
	python3 update_names.py
	gunicorn -w 2 --log-level debug --bind 0.0.0.0:5001 wsgi

sync:
	rsync --delete --exclude='log' --exclude='generated_graphs' --exclude='fetcher_log.txt' --exclude='__pycache__' --exclude='.vscode' --exclude='.DS_Store' --rsh=ssh -aruzhvS . ***REMOVED***@***REMOVED***:~/zzzzz