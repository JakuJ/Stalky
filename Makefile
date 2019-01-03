install: dependencies.txt 
	pip3 install -r dependencies.txt

sync:
	rsync --exclude='log' --exclude='generated_graphs' --exclude='screening.txt' --exclude='__pycache__' --exclude='.vscode' --exclude='.DS_Store' --rsh=ssh -aruzhvS . root@***REMOVED***:~/Desktop/zzzzz