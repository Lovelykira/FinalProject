# FinalProject

Инструкция:<br>
1. git clone https://github.com/Lovelykira/FinalProject.git<br>
2. cd FinalProject/SearchPicsDjango<br>
3. virtualenv -p python3.5 .env<br>
4. pip install -r requirements.txt<br>
5. cd SearchPicsDjango<br>
6. создать local_settings.py с настройками базы данных следующего содержания:<br>
DATABASES = {<br>
    'default': {<br>
    'ENGINE': 'django.db.backends.postgresql_psycopg2',<br>
    'NAME': 'yournewdb',<br>
    'USER': 'yournewuser',<br>
    'PASSWORD': 'whateverpasswordyouenteredearlier',<br>
    'HOST': '', # Set to empty string for localhost.<br>
    'PORT': '', # Set to empty string for default.<br>
    }<br>
}<br>
7. python manage.py migrate<br>
8. cd ../SearchPicsScrapy<br>
9. virtualenv -p python2 .env<br>
10. pip install -r requirements.txt<br>
11. cd ../SearchPicsWebserver<br>
12. virtualenv -p python3.5 .env<br>
13. pip install -r requirements.txt<br>
14. cd ../supervisord<br>
15. mkdir log
16. cd ..
17. sudo apt-get install supervisor<br>
18. supervisord -c supervisord.conf<br>
