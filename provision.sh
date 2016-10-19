#!/usr/bin/env bash
echo "****** Provisioning virtual machine... ******"
cd /vagrant
export DEBIAN_FRONTEND=noninteractive
sudo apt-get --assume-yes install git
sudo apt-get --assume-yes install redis-server
sudo apt-get --assume-yes install python-virtualenv
sudo apt-get --assume-yes install supervisor
sudo apt-get --assume-yes install postgresql
sudo apt-get --assume-yes install libpq-dev python-dev
sudo apt-get --assume-yes install python-dev
sudo apt-get --assume-yes install python3-dev
sudo apt-get --assume-yes install libxml2-dev libxslt1-dev
sudo apt-get --assume-yes install libffi-dev
sudo apt-get --assume-yes install libssl-dev
sudo apt-get --assume-yes install nginx
sudo apt-get --assume-yes install uwsgi
sudo apt-get --assume-yes install uwsgi-plugin-python3
echo "****** Clonning project... ******"
git clone -b virtual_machine https://github.com/Lovelykira/FinalProject.git
git config --global user.email "Lovelykira@gmail.com"
git config --global user.name "kira"
echo "****** Creating virtualenv for Django... ******"
cd FinalProject/SearchPicsDjango
virtualenv -p python3 .env
. .env/bin/activate
pip install -r requirements.txt
deactivate
echo "****** Creating virtualenv for Scrapy... ******"
cd ../SearchPicsScrapy
virtualenv -p python2 .env
. .env/bin/activate
pip install -r requirements.txt
deactivate
echo "****** Creating virtualenv for Web... ******"
cd ../SearchPicsWebserver
virtualenv -p python3 .env
. .env/bin/activate
pip install -r requirements.txt
deactivate
cd ../supervisord
mkdir log
#sudo service nginx start
#cd /vagrant/FinalProject
#supervisord -c supervisord.conf
echo "****** Configurating nginx and uwsi... ******"
ln -s /vagrant/FinalProject/SearchPics_nginx /etc/nginx/sites-enabled/SearchPics_nginx
cp /vagrant/FinalProject/SearchPics_uwsgi.ini /etc/uwsgi/apps-available/SearchPicsDjango.ini
cp /vagrant/FinalProject/uwsi_params /vagrant/uwsgi_params
rm /etc/nginx/nginx.conf
cp ../nginx.conf /etc/nginx/nginx.conf
mkdir /vagrant/log
touch /vagrant/log/nginx.access.log
touch /vagrant/log/nginx.error.log
echo "****** Creating db... ******"
sudo -u postgres psql -c 'CREATE DATABASE spiderdb;'
sudo -u postgres psql -c "CREATE USER kira WITH password '123';"
sudo -u postgres psql -c 'GRANT ALL privileges ON DATABASE spiderdb TO kira;'
echo "****** Django setup... ******"
cd /vagrant/FinalProject/SearchPicsDjango
. .env/bin/activate
cat > SearchPicsDjango/local_settings.py <<EOF
DATABASES = {
'default': {
'ENGINE': 'django.db.backends.postgresql_psycopg2',
'NAME': 'spiderdb',
'USER': 'kira',
'PASSWORD': '123',
'HOST': 'localhost', # Set to empty string for localhost.
'PORT': '', # Set to empty string for default.
}

AWS_ACCESS_KEY_ID = 'AKIAJ4WWLDGCAXCZYUOQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'kira-bucket'

YANDEX_APP_CLIENT_ID = '28b5af656ea54530aa225aeb66123129'
YANDEX_APP_CLIENT_PASS = 'cb7fe3ba115f45ccbe35e391fc0d187d'

PIC_DIR = '/vagrant/user/Projects/'

"ws://127.0.0.1:8003/ws?user_id="
}
EOF
python manage.py migrate
python manage.py collectstatic --noinput
deactivate
cp -f /vagrant/FinalProject/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#sudo start supervisord
#sudo service supervisord start
#supervisord -c /etc/supervisor/supervisord.conf
#supervisorctl start all
#sudo service supervisor start 
sudo supervisord
sudo supervisorctl reload
sudo service nginx restart
