# Электрические и монтажные схемы ЕСКД

Навык для ChatGPT и Codex: подготовка и исправление схем шкафов автоматики, согласование соединений и спецификации, проверка размещения аппаратов и оформления листов.

**Версия пакета: 0.1.0.** Исходники размещены в GitHub. Пакет подготовлен для установки из репозитория; публикация в общем каталоге OpenAI ещё не выполнена. Установка в приложении пользователя проверяется отдельно от проверки файлов пакета.

[Посмотреть учебный комплект — 9 страниц PDF](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/demo/output/demo.pdf) · [Инструкции самого навыка](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/SKILL.md) · [Подготовка публикации в каталоге](docs/publishing.md)

## Возможности и состав

Навык задаёт правила рамок, основных надписей, маркировки цепей, изображения ПЛК, клемм, межшкафных связей и монтажной компоновки. Он помогает сохранять принятые листы при частичных правках и согласовывать Э3/Э4, соединения, перечни и закупочную спецификацию.

В пакет входят инструкции, инструменты Python, шрифты DejaVu Sans с лицензией и самостоятельный вымышленный учебный комплект. Генератор создаёт PDF, DXF, SVG и данные геометрии из общего источника. Средства проверки обнаруживают определённые ошибки соединений, размеров, размещения и фактически экспортированных таблиц.

Это навык черчения и проверки схем. Он не создаёт программы ПЛК. Учебные аппараты и размеры не заменяют документацию конкретного оборудования; `build_demo.py` воспроизводит вложенный пример, а не проектирует произвольный шкаф по одной команде. DXF является редактируемым обменным форматом, но не собственным файлом КОМПАС CDW. Проверка скриптами не подтверждает автоматически полное соответствие ГОСТ, электрическую безопасность или пригодность промышленного проекта.

## Быстрая установка отдельного навыка в Codex

Вставьте в новый диалог Codex:

```text
$skill-installer Установи навык eskd-electrical-cabinets из репозитория https://github.com/Solute666/eskd-electrical-cabinets, папка plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets. Проверь, что скопированы scripts, references и assets вместе с SKILL.md.
```

Проверьте появление навыка через `/skills` или выбор после `$`. Если он не появился, перезапустите Codex. Для запуска включённых скриптов потребуется Python с зависимостями ниже; установка навыка сама по себе не устанавливает библиотеки Python.

При ручной установке скопируйте **всю папку** `plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets` в пользовательскую папку `~/.agents/skills/`. В Windows это папка `.agents/skills` в профиле пользователя. Для установки только в один проект используйте `<проект>/.agents/skills/eskd-electrical-cabinets/`.

Выберите один способ установки: одновременная установка отдельного навыка и содержащего его плагина может создать две записи с одинаковым названием.

## Установка пакета плагина

Плагин содержит тот же навык. В терминале с установленным актуальным Codex CLI добавьте каталог этого репозитория:

```bash
codex plugin marketplace add Solute666/eskd-electrical-cabinets --ref main
```

После этого в поддерживаемом настольном приложении ChatGPT откройте каталог плагинов, выберите источник **Solute666 — инженерные навыки** и установите **Электрические схемы ЕСКД**. При необходимости перезапустите приложение. Команда добавляет источник каталога; сама установка и проверка выполняются следующим шагом в приложении.

Доступность локальных каталогов зависит от приложения и настроек рабочей области. Эта инструкция не означает, что загрузка репозитория автоматически установит навык в любой веб-аккаунт ChatGPT. Для распространения через общий каталог ChatGPT/Codex нужна отдельная публикация: [порядок действий](docs/publishing.md).

## Первый запрос

После установки отдельного навыка в Codex:

```text
$eskd-electrical-cabinets Воспроизведи вложенный учебный комплект в отдельной рабочей папке. Используй штатный build_demo.py, проверь выпуск через audit_release.py, покажи PDF и перечисли выполненные проверки. Не меняй установленный навык.
```

Для проверки своего проекта приложите схемы, действующую спецификацию и доступную документацию оборудования:

```text
$eskd-electrical-cabinets Проверь приложенный комплект: маркировку цепей, выводы ПЛК, клеммы, межшкафные соединения, размещение аппаратов и согласованность со спецификацией. Сначала назови подтверждённые расхождения, затем исправь затронутые листы. Сохрани принятые листы и выдай PDF вместе с редактируемыми исходниками.
```

В ChatGPT выбирайте установленный навык или плагин через `@`; название для выбора подскажет интерфейс.

## Воспроизведение примера без диалога

Проверенная среда исходного навыка: Python 3.12.14, ReportLab 4.4.9, PyMuPDF 1.26.6, ezdxf 1.4.4. Команды ниже выполняются из корня клонированного репозитория, где находятся этот README и папка `plugins`. В Windows используйте установленный интерпретатор `python` или замените его на `py -3.12`.

Создайте виртуальное окружение и активируйте его:

```bash
python -m venv .venv
```

В Linux/macOS: `source .venv/bin/activate`. В PowerShell: `.\.venv\Scripts\Activate.ps1`. Если политика PowerShell блокирует активацию, можно запускать `.\.venv\Scripts\python.exe` напрямую вместо `python`.

```bash
python -m pip install -r plugins/eskd-electrical-cabinets/requirements.txt
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/verify_references.py
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/build_demo.py --out work/demo
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/audit_release.py plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/demo/project.json --bundle work/demo --report work/qa/release.json
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/self_check.py --bundle work/demo
```

Результат: `work/demo/demo.pdf`, отдельные листы PDF/DXF/SVG, данные геометрии и `release.json`. Рабочие файлы записываются вне установленного навыка. Генерация не требует запуска системы автоматизированного проектирования; для просмотра и редактирования DXF используйте подходящее приложение.

## Проверки и ограничения

Самопроверка содержит 32 случая, включая преднамеренные ошибки. Она проверяет способность средств контроля обнаруживать эти ошибки, а не все возможные инженерные ошибки. Проверка эталонных файлов сравнивает контрольные суммы 39 файлов. Проверка выпуска читает данные из экспортированных файлов и сопоставляет их с моделью.

[Отчёт подготовки этой публикации](docs/validation.json) фиксирует реально выполненные проверки. [Отчёт разработки навыка](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/validation-report.json) сохранён отдельно как часть исходного пакета. Обязательны просмотр изменённых листов и проверка исходных данных оборудования. Печать на конкретном принтере отдельно не испытывалась.

## Сборка ZIP для каталога

```bash
python tools/build_plugin.py
```

Команда создаёт `dist/eskd-electrical-cabinets-0.1.0.zip`. В корне архива находятся `plugin.json`, `requirements.txt` и папка `skills`. История Git, временные файлы, кэш Python и рабочие проекты в архив не попадают. ZIP не хранится второй копией исходников в репозитории. Проверки содержимого и публичная заявка описаны в [docs/publishing.md](docs/publishing.md).

## Авторство и лицензии

Владелец репозитория: [Solute666](https://github.com/Solute666). Лицензия на авторские инструкции, инструменты и учебный пример пока не выбрана владельцем; в версии 0.1.0 она не объявлена. Условия дальнейшего распространения следует согласовать с владельцем.

Шрифты распространяются по собственной [включённой лицензии DejaVu](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/fonts/LICENSE.txt). Библиотеки Python устанавливаются отдельно и сохраняют свои лицензии.

## Официальные инструкции

- [Навыки и их установка](https://learn.chatgpt.com/docs/build-skills).
- [Упаковка плагина и каталоги репозиториев](https://developers.openai.com/plugins/build/plugins).
- [Отправка плагина на рассмотрение](https://developers.openai.com/plugins/deploy/submission).

Инструкции по платформе сверены 11 октября 2026 года. Поддержка функций в конкретном клиенте и рабочей области может отличаться.

## English overview

This repository packages a Russian-language ESKD electrical and wiring drawing skill for automation cabinets. It includes instructions, Python drawing and audit tools, bundled licensed fonts, and a fictional nine-sheet PDF/DXF/SVG example. Install the standalone skill from `plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets`, or use the repository plugin marketplace. Public OpenAI directory submission is pending. The skill does not program PLCs or certify electrical designs. No license has yet been selected for the authored materials; bundled fonts retain their included license.
