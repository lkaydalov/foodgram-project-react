![foodgram-project-react workflow](https://github.com/lkaydalov/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)


## Ссылка на развернутый проект
```
http://158.160.24.105/secure/
http://lkaydalov.ddns.net/admin/
```

# Проект Foodgram
Сервис 
## Описание
Пользователи сервиса 
## Технологии
Python 3.9
Django 2.2.19

## Запуск проекта в контейнере
- Перенесите из проекта файлы docker-compose.yaml и nginx.conf на сервер виртуальной машины
```
scp docker-compose.yaml <your_username>@<your_server_ip>:/home/<your_server_login>
scp nginx.conf <your_username>@<your_server_ip>:/home/<your_server_login>
```
- Если на сервере уже запущен nginx - остановите его
```
sudo systemctl stop nginx
```
- Загрузите на сервер последний образ web
```
sudo docker pull <dockerhub_login>/<container_name>:<tag>
```
- Запустите 3 контейнера на основе образа (контейнер с сервером nginx, контейнер с образом postgresql, контейнер с проектом):
```
docker-compose up -d --build
```
- Теперь в контейнере backend выполните миграции, создайте суперпользователя, соберите статику, и загрузите данные из БД
```
sudo docker-compose exec backend python manage.py migrate
sudo docker-compose exec backend python manage.py createsuperuser
sudo docker-compose exec backend python manage.py collectstatic --no-input
sudo docker-compose exec backend python manage.py loaddata dump.json
```
## Шаблон наполнения .env файла
```
SECRET_KEY=#задайте свой секретный ключ
DB_ENGINE=django.db.backends.postgresql 
DB_NAME=postgres 
POSTGRES_USER=postgres 
POSTGRES_PASSWORD=#задайте свой пароль 
DB_HOST=db 
DB_PORT=5432 
```