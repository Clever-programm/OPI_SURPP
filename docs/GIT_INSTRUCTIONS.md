# Руководство по работе с Git и GitHub для команды

Это руководство объясняет:
- как установить и использовать Git
- как работать с Git в VS Code и терминале
- как работать с GitHub
- правила разработки в нашем проекте

---

# Содержание

1. Установка Git
2. Первоначальная настройка Git
3. Работа с репозиторием
4. Работа через VS Code
5. Работа через терминал
6. Работа с GitHub
7. Процесс разработки в нашем проекте
8. Правила именования веток
9. Правила именования коммитов
10. Полный пример рабочего процесса

---

# 1. Установка Git

## Windows
Скачать: https://git-scm.com/download/win

Установить со стандартными настройками.

## Linux

Ubuntu / Debian:

```bash
sudo apt install git
````

Arch:

```bash
sudo pacman -S git
```

Fedora:

```bash
sudo dnf install git
```

## MacOS

```bash
brew install git
```

или установить Xcode Command Line Tools:

```bash
xcode-select --install
```

---

# 2. Первоначальная настройка Git

Выполнить ОДИН РАЗ:

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "your@email.com"
```

Проверить:

```bash
git config --list
```

---

# 3. Клонирование репозитория

Скопировать ссылку с GitHub и выполнить:

```bash
git clone https://github.com/Clever-programm/OPI_SURPP.git
```

Перейти в папку:

```bash
cd OPI_SURPP
```

---

# 4. Работа через VS Code (рекомендуется новичкам)

## Открыть проект

File → Open Folder → выбрать папку проекта

## Вкладка Source Control

Иконка слева:
`Ctrl + Shift + G`

Там можно:

* видеть изменения
* писать commit message
* делать commit
* делать push
* делать pull

---

## Commit в VS Code

1. Изменить файлы
2. Открыть Source Control
3. Ввести сообщение commit
4. Нажать "Commit"
5. Нажать "Push"

---

# 5. Работа через терминал

## Проверить изменения

```bash
git status
```

## Добавить изменения

```bash
git add .
```

или конкретный файл:

```bash
git add file.py
```

## Сделать commit

```bash
git commit -m "feat: add login logic"
```

## Отправить на GitHub

```bash
git push
```

## Получить изменения

```bash
git pull
```

---

# 6. Работа с ветками

## Посмотреть ветки

```bash
git branch
```

## Создать ветку из dev

```bash
git checkout dev
git pull
git checkout -b 123_add-login
```

## Переключиться на ветку

```bash
git checkout branch_name
```

## Отправить ветку на GitHub

```bash
git push -u origin branch_name
```

---

# 7. Работа с GitHub

GitHub используется для:

* хранения кода
* задач (Issues)
* Pull Requests (PR)
* code review

---

# 8. Где брать задачи

Задачи находятся во вкладке:

GitHub → Issues

Каждая задача имеет номер:

```
#123 Добавить авторизацию
```

Этот номер используется в имени ветки.

---

# 9. Как создать ветку под задачу

Структура имени ветки:

```
<номер задачи>_<краткое-имя>
```

Примеры:

```
123_add-login
45_fix-auth-bug
78_create-database
```

Создание:

```bash
git checkout dev
git pull
git checkout -b 123_add-login
```

---

# 10. Процесс разработки

Полный цикл:

### 1. Перейти на dev

```bash
git checkout dev
git pull
```

### 2. Создать ветку

```bash
git checkout -b 123_add-login
```

### 3. Работать, делать commits

```bash
git add .
git commit -m "feat(auth): add login logic"
```

### 4. Отправить ветку

```bash
git push
```

### 5. Создать Pull Request

GitHub → Pull Requests → New Pull Request

BASE: `dev`
COMPARE: `123_add-login`

Создать PR.

---

# 11. Pull Request (PR)

PR используется для слияния ветки в dev.

Нельзя пушить напрямую в dev.

Только через PR.

PR должен содержать:

* описание
* что сделано
* номер задачи

Пример:

```
Добавлена логика авторизации

Closes #123
```

---

# 12. Правила веток (ВАЖНО)

В нашем проекте используются 3 типа веток:

---

## main

Основная ветка.

ЗАПРЕЩЕНО:

* commit
* push
* merge

Используется только для стабильных версий.

---

## dev

Ветка разработки / релиза.

ЗАПРЕЩЕНО:

* commit напрямую
* push напрямую

РАЗРЕШЕНО:

* создавать ветки из dev
* делать PR в dev

---

## feature ветки

Создаются из dev.

Структура:

```
<номер задачи>_<название>
```

Пример:

```
123_add-login
```

---

# 13. Правила commit сообщений

Структура:

```
<префикс>(<область>): <описание>
```

область — опционально

---

## Примеры

```
feat: add login system
feat(auth): add JWT logic

fix: fix crash on startup
fix(api): fix user endpoint

docs: update README

refactor: simplify auth logic

style: format code

test: add login tests

chore: update dependencies
```

---

# 14. Префиксы commit

Основные:

```
feat     — новая функциональность
fix      — исправление бага
docs     — документация
refactor — рефакторинг
style    — форматирование
test     — тесты
chore    — служебные изменения
```

Дополнительно:

```
perf     — улучшение производительности
ci       — изменения CI/CD
build    — изменения сборки
```

---

# 15. Примеры хороших commit

Хорошо:

```
feat(auth): add login endpoint
fix(api): fix null pointer exception
docs: add setup guide
```

Плохо:

```
fix
update
changes
asdf
```

Commit должен объяснять ЧТО сделано.

---

# 16. Полный пример работы

Получили задачу:

```
#123 Добавить авторизацию
```

Выполняем:

```bash
git checkout dev
git pull

git checkout -b 123_add-login

# работаем

git add .
git commit -m "feat(auth): add login endpoint"

git push
```

Создаем PR:

```
FROM: 123_add-login
TO: dev
```

---

# 17. Основные правила проекта (кратко)

ЗАПРЕЩЕНО:

* push в main
* push в dev
* commit в dev
* commit в main
* работать без ветки

ОБЯЗАТЕЛЬНО:

* ветка под каждую задачу
* PR в dev
* понятные commit сообщения

---

# 18. Если что-то сломалось

Можно отменить изменения:

```bash
git restore .
```

Или спросить тимлида.

---

# 19. Рекомендуемый workflow

Всегда:

```
dev → feature branch → PR → dev
```

НИКОГДА:

```
dev → commit → push ❌
main → commit → push ❌
```

---

# Готово

Следуйте этому руководству.
Это обязательно для всех участников проекта.