.PHONY: install server rename sync 

install: dependencies.txt 
	pip3 install -r dependencies.txt

server: wsgi.py app.py update_names.py graph.py
	python3 update_names.py
	python3 graph.py
	gunicorn -w 2 --log-level debug --bind 0.0.0.0:5001 wsgi

rename:
	sed -i -e 's/webStatus/vc_0/g' log/*
	sed -i -e 's/fbAppStatus/vc_8/g' log/*
	sed -i -e 's/messengerStatus/vc_10/g' log/*
	sed -i -e 's/otherStatus/vc_74/g' log/*

sync:
	rsync --delete --exclude='log' --exclude='generated_graphs' --exclude='screening.txt' --exclude='__pycache__' --exclude='.vscode' --exclude='.DS_Store' --rsh=ssh -aruzhvS . root@***REMOVED***:~/Desktop/zzzzz