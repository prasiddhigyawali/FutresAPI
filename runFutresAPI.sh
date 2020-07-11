source /home/jdeck/.bashrc
cd /home/jdeck/code/FutresAPI
git pull
/usr/bin/sudo -u jdeck -i python /home/jdeck/code/FutresAPI/fetch.py
git add -A
git commit -m "updating based on automatic fetch process"
git push
