.PHONY: install server rename sync 

install:
	pip3 install -r dependencies.txt

server:
	python3 update_names.py
	gunicorn -w 2 --log-level debug --bind 0.0.0.0:5001 wsgi

rename:
	sed --in-place 's/webStatus/vc_0/g' log/*
	sed --in-place 's/fbAppStatus/vc_8/g' log/*
	sed --in-place 's/messengerStatus/vc_74/g' log/*
	sed --in-place 's/otherStatus/vc_10/g' log/*

sync:
	rsync --delete --exclude='log' --exclude='generated_graphs' --exclude='screening.txt' --exclude='__pycache__' --exclude='.vscode' --exclude='.DS_Store' --rsh=ssh -aruzhvS . root@***REMOVED***:~/Desktop/zzzzz