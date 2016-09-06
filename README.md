# FinalProject

Инструкция:<br>
1. git clone https://github.com/Lovelykira/FinalProject.git<br>
2. cd FinalProject/SearchPicsDjango<br>
3. virtualenv -p python3.5 .env<br>
4. pip install requirements.txt<br>
5. cd SearchPicsDjango<br>
6. crсоздать local_settings.py с настройками базы данных следующего содержания:<br>
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
7. python manage.py makemigrations<br>
8. python manage.py migrate<br>
9. cd ../SearchPicsScrapy<br>
10. virtualenv -p python2 .env<br>
11. pip install requirements.txt<br>
12. cd ../SearchPicsWebserver<br>
13. virtualenv -p python3.5 .env<br>
14. pip install requirements.txt<br>
15. cd ..<br>
16. easy_install supervisor<br>
17. supervisord -c supervisord.conf<br>
