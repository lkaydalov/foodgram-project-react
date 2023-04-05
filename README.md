![foodgram-project-react workflow](https://github.com/lkaydalov/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)


## Ссылка на развернутый проект
```
http://158.160.24.105/secure/
http://lkaydalov.ddns.net/secure/
http://lkaydalov.ddns.net
```

## Проект Foodgram
Продуктовый помощник Foodgram. Здесь пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять их в "Избранное", а также скачивать сводный список продуктов, необходимых для приготовления блюд.

## Технологии

| Python 3.7 | Django 2.2.19 | Django Rest Framework 3.12.4 |
|----------------|:---------:|----------------:|
| **Nginx** | **Gunicorn** | **PostgreSQL** |
| **Docker-compose** | **Docker Hub** | **Github Acton** |

## Запуск проекта в контейнере
- Перенесите из локального проекта файлы docker-compose.yaml и nginx.conf на сервер виртуальной машины
```
scp docker-compose.yaml <your_username>@<your_server_ip>:/home/<your_server_login>
scp nginx.conf <your_username>@<your_server_ip>:/home/<your_server_login>
```
- Если на сервере уже запущен nginx - остановите его
```
sudo systemctl stop nginx
```
- Если на сервере запущены контейнеры - удалите их
```
sudo docker-compose rm backend
sudo docker-compose rm frontend
```
- Удалите файл с переменными окружения, если он есть на сервере, и создайте новый:
```
rm .env -f
touch .env
echo SECRET_KEY=your.SECRET_KEY >> .env
echo DB_ENGINE=your.DB_ENGINE >> .env
echo DB_NAME=your.DB_NAME >> .env
echo POSTGRES_USER=your.POSTGRES_USER >> .env
echo POSTGRES_PASSWORD=your.POSTGRES_PASSWORD >> .env
echo DB_HOST= your.DB_HOST >> .env
echo DB_PORT=your.DB_PORT >> .env
```
- Загрузите на сервер последний образ backend, затем frontend
```
sudo docker pull <dockerhub_login>/<container_name>:<tag>
```
- Запустите 4 контейнера (контейнер с сервером nginx, контейнер с образом postgresql, контейнер с бекендом проекта, контейнер с фронтендом проекта):
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
SECRET_KEY=#'секретный ключ проекта'
DB_ENGINE=django.db.backends.postgresql 
DB_NAME=postgres 
POSTGRES_USER=postgres 
POSTGRES_PASSWORD=#задайте свой пароль
DB_HOST=db 
DB_PORT=5432 
```

## Описание ендпоинтов доступно по адресу:

[lkaydalov.ddns.net/api/docs/](http://lkaydalov.ddns.net/api/docs/)
