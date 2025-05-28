# Foodgram IsakovLA

## Требования
- Docker
- Docker Compose

## Установка и запуск

1. **Клонирование репозитория на локальную тачку**
2. **Скопируйте пример файла `.env` из `env.testexample`**
3. **Запуск приложения**
   ```bash
   docker-compose -f ./docker-compose.deploy.yml up
   ```
   После запуска приложение будет доступно по адресу: [http://localhost](http://localhost)

## Создание админки

1. Войдите в контейнер:
   ```bash
   docker exec -it backend sh
   ```

2. Создайте суперпользователя:
   ```bash
   python manage.py createsuperuser
   ```
   Заполните необходимые поля (логин, email, пароль).

3. Админка будет доступна по адресу: [http://localhost/admin](http://localhost/admin)

## Документация API
Документация Redoc доступна по адресу: [http://localhost/api/docs/](http://localhost/api/docs/)

## Тестирование API через Postman
Инструкция по тестированию API находится в файле:  
`./postman_collection/README.md`
