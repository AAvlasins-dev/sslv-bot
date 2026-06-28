# Деплой бота на Oracle Cloud (Always Free) — 24/7

Бот работает на long-polling + фоновый мониторинг, поэтому ему нужен сервер,
который **не засыпает**. Oracle Cloud Always Free даёт бесплатную виртуальную
машину навсегда — идеально подходит.

Бот **только исходящие** соединения (опрашивает Telegram и ss.lv), входящие
порты открывать **не нужно** — никакого веб-сервера.

---

## 1. Создать аккаунт Oracle Cloud

1. Зайди на https://www.oracle.com/cloud/free/ → **Start for free**.
2. Регистрация: email, страна (Latvia), номер телефона.
3. Привязать карту — нужна **только для верификации** (списывается ~0–1 € и
   возвращается). Тариф **Always Free** не списывает деньги, пока ты не нажмёшь
   «Upgrade to Paid» вручную.
4. Выбери home region поближе (например **Frankfurt** или **Amsterdam**).

---

## 2. Создать виртуальную машину (Always Free)

В консоли Oracle: **Menu → Compute → Instances → Create instance**.

- **Name:** `sslv-bot`
- **Image:** Canonical **Ubuntu 22.04** (или 24.04)
- **Shape → Change shape:**
  - Лучший вариант: **Ampere (ARM) — VM.Standard.A1.Flex**, поставь
    **1 OCPU / 6 GB RAM** (входит в Always Free, с запасом).
  - Если пишет *“Out of capacity”* (часто бывает с ARM) — выбери
    **AMD — VM.Standard.E2.1.Micro** (1/8 OCPU, 1 GB). Для этого бота хватает.
- **SSH keys:** нажми **Save private key** (скачается файл `ssh-key-*.key`) —
  он понадобится для входа. Публичный ключ Oracle добавит сам.
- **Create.**

Через ~1 минуту у инстанса появится **Public IP address** — запиши его.

---

## 3. Подключиться по SSH

На своём компьютере (PowerShell в папке, куда скачался ключ):

```powershell
# один раз ограничить права на ключ (иначе SSH ругается)
icacls .\ssh-key-2026-*.key /inheritance:r /grant:r "$($env:USERNAME):(R)"

ssh -i .\ssh-key-2026-*.key ubuntu@ВАШ_PUBLIC_IP
```

Пользователь на Ubuntu-образе — `ubuntu`.

---

## 4. Установить Docker (на сервере)

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# перелогиниться, чтобы группа docker применилась:
exit
```
Зайди по SSH снова (тот же `ssh -i ... ubuntu@IP`).

Проверка: `docker run --rm hello-world` должно вывести “Hello from Docker!”.

---

## 5. Склонировать бота и задать токен

```bash
git clone https://github.com/AAvlasins-dev/sslv-bot.git
cd sslv-bot

# создать .env из примера и вписать свой токен от @BotFather
cp .env.example .env
nano .env
```
В `nano` укажи свой `BOT_TOKEN=...` (остальное можно оставить как есть —
`DB_PATH` для Docker уже принудительно ставится в `docker-compose.yml`,
так что путь в `.env` роли не играет). Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## 6. Запустить

```bash
docker compose up -d --build
```
Первая сборка займёт несколько минут (ставятся зависимости). Дальше:

```bash
docker compose logs -f          # смотреть логи (выход — Ctrl+C)
docker compose ps               # статус контейнера
```
В логах должно появиться `ss.lv monitor started`. Напиши боту в Telegram — он
ответит.

`restart: unless-stopped` + включённый сервис Docker означают, что бот
**сам поднимется после перезагрузки сервера**.

База `data.db` (фильтры, пользователи) лежит на сервере в `./data/` и
переживает пересборки и ребуты.

---

## 7. Обновление бота в будущем

Когда поправишь код локально и запушишь в GitHub:

```bash
cd ~/sslv-bot
git pull
docker compose up -d --build
```

---

## Полезные команды

| Действие                     | Команда                                  |
|------------------------------|------------------------------------------|
| Логи в реальном времени      | `docker compose logs -f`                 |
| Остановить                   | `docker compose down`                    |
| Запустить                    | `docker compose up -d`                   |
| Перезапустить                | `docker compose restart`                 |
| Бэкап базы                   | `cp data/data.db ~/data.db.bak`          |
| Занятое место                | `df -h` / `docker system df`             |

---

## Если что-то не так

- **Контейнер сразу падает** → `docker compose logs` покажет причину. Чаще
  всего — не вписан или неверный `BOT_TOKEN` в `.env`.
- **`docker: permission denied`** → не перелогинился после `usermod -aG docker`
  (шаг 4). Выйди по SSH и зайди снова.
- **Бот не отвечает, но контейнер running** → проверь, что токен правильный и
  бот не запущен где-то ещё одновременно (Telegram разрешает только один
  polling на токен).
