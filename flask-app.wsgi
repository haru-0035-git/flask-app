import sys
import os


# Flaskアプリケーションが存在するディレクトリをPythonパスに追加
sys.path.insert(0, '/var/www/html/flask-app')

# 仮想環境のPythonパスを追加
sys.path.insert(0, '/var/www/html/flask-app/flask-env/lib/python3.12/site-packages')




# Flaskアプリケーションのインポート
from app import app as application
