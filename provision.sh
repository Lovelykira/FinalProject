#!/usr/bin/env bash
echo "****** Provisioning virtual machine... ******"
cd /vagrant
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
echo "****** Creating virtualenv for Scrapy... ******"
cd ../SearchPicsScrapy
virtualenv -p python2 .env
pip install -r requirements.txt
echo "****** Creating virtualenv for Web... ******"
cd ../SearchPicsWebserver
virtualenv -p python3 .env
pip install -r requirements.txt
cd ../supervisord
mkdir log
#sudo service nginx start
#cd /vagrant/FinalProject
#supervisord -c supervisord.conf
echo "****** Configurating nginx and uwsi... ******"
ln -s /vagrant/FinalProject/SearchPics_nginx /etc/nginx/sites-enabled/SearchPicsDjango
cp /vagrant/FinalProgect/SearchPics_uwsgi.ini /etc/uwsgi/apps-available/SearchPicsDjango.ini
