# Изолированное развёртывание AIpedia

Исторические шаблоны первоначальной установки. **Сайт уже работает; эти шаги повторять не нужно.**
20.09.2026 подтверждены `/srv/aipedia/app`, `/srv/aipedia/data/aipedia.sqlite3` и выделенный
Supervisor с программами aipedia, aipedia-backup, aipedia-tunnel. Текущий выпуск выполняется
через `tools/deploy_release.py` с SHA256 архива, online-backup и остановкой только aipedia.
Фактический статус и следующий шаг — `docs/EXECUTION_STATE.md`.

## Проверенное и неизвестное

18 сентября 2026 просмотрен локальный `NT-Analyzer/deploy/canary/README.md`.
Раздел Real host topology note от 11 августа описывает root supervisord
без systemd и Cloudflare Tunnel. Это документация, не свежая SSH-проверка.
Адрес действующего приложения: `app.stratforges.com`; это публичный адрес,
он сам по себе не раскрывает origin-хост за Tunnel.

В этой задаче SSH-хост/подключение не обнаружены. До выбора окончательной
конфигурации выполнить `python3 preflight.py` непосредственно на сервере.
Скрипт только читает имя init-процесса, наличие Supervisor/cloudflared,
ресурсы и занятость предложенного порта. Он не читает ключи или окружения.
Нужны ещё фактический путь Supervisor include и выбранный домен.

## Схема

Отдельный домен -> отдельный Cloudflare Named Tunnel ->
127.0.0.1:18810 -> Waitress/Django -> /srv/aipedia/data/aipedia.sqlite3

- Linux-пользователь: `aipedia`, без прав на каталоги StratForge.
- Release: `/srv/aipedia/releases/<release>`; ссылка `current` только внутри AIpedia.
- Данные: `/srv/aipedia/data`; резервные копии: `/srv/aipedia/backups`.
- Секреты: `/srv/aipedia/config/aipedia.env`, права 600, вне Git.
- Supervisor: программа `aipedia-web`, отдельные логи и ограничения.
- Отдельные tunnel credentials и hostname; не редактировать существующий tunnel.
- Для чтения и редких редакторских записей достаточно SQLite на локальном диске.
  При нескольких экземплярах приложения перейти на отдельную PostgreSQL-базу.

## Последовательность после проверки хоста и приёмки

1. Назначить новый домен и проверить доступные ресурсы/порт через `preflight.py`.
2. Создать пользователя и каталоги AIpedia с изолированными правами.
3. Перенести release, создать venv и установить `requirements.lock`.
4. Заполнить `aipedia.env` по примеру; ключ генерировать через
   `python -c "import secrets; print(secrets.token_urlsafe(64))"` в приватном терминале.
5. Под этим окружением выполнить `manage.py migrate`, `seed_catalog`,
   `collectstatic --noinput`, `createsuperuser`, `check --deploy`.
6. Скопировать отдельный `supervisor.conf.example` в подтверждённый include.
   `supervisorctl reread`, затем `supervisorctl update aipedia-web`.
   Никогда не использовать `restart all` или `update` без имени группы.
7. Проверить `/healthz`, страницы, статику, вход редактора на loopback.
8. Создать отдельный Named Tunnel и DNS-запись выбранного hostname;
   пример `cloudflared.yml.example` запускается отдельной службой.
9. Перед публикацией закрыть `/admin/*` через Cloudflare Access, добавить
   ограничение POST `/report` на edge; локальная задержка формы привязана
   к сессии и не заменяет ограничение по источнику запросов.
10. Проверить TLS/redirect/cookies, внешние ссылки и мобильный вид на домене.
11. Сохранить исходные статусы и повторно проверить работоспособность StratForge.

Для проверки HTTP-origin в production нужен заголовок `X-Forwarded-Proto: https`.
Он принимается только от доверенного loopback-прокси. Порт не публиковать наружу.
Шаблон cloudflared нужно установить отдельно после проверки supervisor topology.

## Резервирование и откат

`python tools/backup.py` использует SQLite Online Backup API: файл не копируется
в середине транзакции. Запускать ежедневно средствами подтверждённого хоста.
Путь назначения задаётся `--output`; по умолчанию внутри каталога AIpedia.
Копии содержат пользователей и сообщения редакции; доступ только владельцу
сервиса. Настроить защищённое внешнее хранение и срок хранения до публикации.

При ошибке приложения остановить только `aipedia-web`, переключить `current`
на предыдущий релиз, запустить только эту программу. Перед несовместимой
миграцией создать копию; восстановление БД выполнять при остановленном AIpedia.
Текущая миграция начальная. StratForge БД, процессы, маршруты и файлы не нужны.
