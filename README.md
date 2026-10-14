# Электрические и монтажные схемы ЕСКД

Навык для ChatGPT и Codex: подготовка и исправление схем шкафов автоматики, согласование соединений и спецификации, проверка размещения аппаратов и оформления листов.

**Версия пакета: 0.2.0.** Обновление с проектным образцом X2002 доступно в этом репозитории. Владелец разрешил публичную загрузку включённых материалов 14 октября 2026 года. Публикация в общем каталоге OpenAI ещё не выполнена. Установка в приложении пользователя проверяется отдельно от проверки файлов пакета.

[Электрическая схема — 11 страниц PDF](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/x2002-reference/documents/X2002_ШС1_Э3_Р27_Комплект.pdf) · [Монтажная схема — 12 страниц PDF](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/x2002-reference/documents/X2002_ШС1_Монтажная_схема_Р31.pdf) · [Инструкции самого навыка](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/SKILL.md) · [Подготовка публикации в каталоге](docs/publishing.md)

## Возможности и состав

Навык задаёт правила рамок, основных надписей, маркировки цепей, изображения ПЛК, клемм, межшкафных связей и монтажной компоновки. Он помогает сохранять принятые листы при частичных правках и согласовывать Э3/Э4, соединения, перечни и закупочную спецификацию.

В версии 0.2.0 основной образец — реальный комплект ПАККА / X2002 до замены покупного шкафа оператора на самодельный: 14 документов, суммарно 57 страниц PDF, проектные модели и пять архивов исходников. Силовые шкафы имеют размер 1200×800×400 мм, покупные шкафы оператора — 500×400×200 мм. Эти значения относятся только к образцу. Принятые чертежи и исторические редакции сохранены; перечень поставки синхронизирован с составом и спецификацией.

Известное исключение — шаг осей коробов у DIN3 270 мм; его нельзя переносить в новые проекты как общее правило. Подробные границы применения находятся в [описании образца](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/references/sample-scope.md). Архивы сохраняют исторические зависимости; окончательные документы выбираются по [реестру комплекта](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/x2002-reference/set-manifest.json).

`rebuild_reference.py` воспроизводит электрический комплект либо монтажный выпуск в отдельной папке. Для монтажного выпуска заново строится лист 1, а листы 2–12 сохраняются исходным генератором. `build_validation_fixture.py` создаёт технический набор для проверки инструментов; этот набор не используется как образец оформления. Прежний `build_demo.py` удалён.

Включены инструменты Python и шрифты DejaVu Sans с лицензией. Общий генератор создаёт PDF, DXF, SVG и данные геометрии из общего источника. Это навык подготовки схем, программирование ПЛК в него не входит. DXF не является собственным файлом КОМПАС CDW. Проверки не подтверждают автоматически все электрические расчёты, безопасность или полное соответствие ГОСТ.

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
$eskd-electrical-cabinets Воспроизведи электрический комплект проектного образца X2002 в отдельной пустой рабочей папке через rebuild_reference.py --part electrical. Проверь состав через verify_reference_set.py, сравни созданный PDF с эталоном и покажи результат. Не меняй установленный навык.
```

Для проверки своего проекта приложите схемы, действующую спецификацию и доступную документацию оборудования:

```text
$eskd-electrical-cabinets Проверь приложенный комплект: маркировку цепей, выводы ПЛК, клеммы, межшкафные соединения, размещение аппаратов и согласованность со спецификацией. Сначала назови подтверждённые расхождения, затем исправь затронутые листы. Сохрани принятые листы и выдай PDF вместе с редактируемыми исходниками.
```

В ChatGPT выбирайте установленный навык или плагин через `@`; название для выбора подскажет интерфейс.

## Воспроизведение образца без диалога

Команды выполняются из корня клонированного репозитория. Проверенные версии: Python 3.12.14, ReportLab 4.4.9, PyMuPDF 1.26.6, ezdxf 1.4.4. Добавлен openpyxl 3.1.5 для чтения XLSX при проверке комплекта. В Windows используйте установленный `python` или `py -3.12`.

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

В Linux/macOS активируйте его командой `source .venv/bin/activate`. В PowerShell: `.\.venv\Scripts\Activate.ps1`. Если активация недоступна, можно запускать `.\.venv\Scripts\python.exe` напрямую вместо `python`.

```bash
python -m pip install -r plugins/eskd-electrical-cabinets/requirements.txt
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/verify_references.py
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/verify_reference_set.py plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/x2002-reference --report work/qa/reference-set.json
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/rebuild_reference.py --part electrical --out work/electrical
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/rebuild_reference.py --part mounting --out work/mounting
```

Для каждого воспроизведения нужна отдельная пустая папка. При повторном запуске выбирайте новое имя, например `work/electrical-02`. Скрипт не перезаписывает прежнюю работу. Отчёт сравнения находится в `reproduction.json`, журнал — в `build.log`, а PDF и другие экспорты — в подпапке проекта `output`.

## Техническая проверка инструментов

```bash
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/build_validation_fixture.py --out work/validator
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/audit_release.py plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/test_fixtures/validator_project.json --bundle work/validator --report work/qa/validator-release.json
python -B plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/scripts/self_check.py --bundle work/validator
```

Этот искусственный набор проверяет инструменты. Подробные листы X2002 остаются основным визуальным образцом.

## Проверки и ограничения

Самопроверка инструментов содержит 32 случая, включая преднамеренные ошибки. Проверка эталонных ресурсов сверяет 40 файлов. `verify_reference_set.py` проверяет 14 документов, 99 позиций, 300 соединений, 183 клеммы, состав и габариты корпусов, а также читает 400 ячеек из PDF перечня поставки.

[Отчёт подготовки публикации](docs/validation.json) фиксирует реально выполненные проверки и статус публичного разрешения. [Отчёт разработки навыка](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/validation-report.json) сохранён отдельно. Хеш подтверждает идентичность файла, а не инженерную правильность. Исторические отчёты ограничены заявленным в них объёмом.

Глубина компоновки, тепловые расчёты, отверстия, безопасность и достаточность кабельных вводов требуют отдельных проверок. Достоверность паспортных данных оборудования, просмотр изменённых листов и печать на конкретном принтере автоматически не подтверждаются.

## Сборка ZIP для каталога

```bash
python tools/build_plugin.py
```

Команда создаёт `dist/eskd-electrical-cabinets-0.2.0.zip`. В корне архива находятся `plugin.json`, `requirements.txt` и папка `skills`. История Git, временные файлы, кэш Python и рабочие проекты в архив не попадают. Пять зафиксированных архивов исходников X2002 включаются только после проверки их контрольных сумм, целостности и путей; неизвестные вложенные архивы блокируются. Эта техническая проверка не заменяет разрешение на публичное распространение. ZIP не хранится второй копией исходников в репозитории. Проверки содержимого и публичная заявка описаны в [docs/publishing.md](docs/publishing.md).

## Авторство и лицензии

Владелец репозитория: [Solute666](https://github.com/Solute666). Лицензия на авторские инструкции, инструменты и учебный пример пока не выбрана владельцем; в версии 0.2.0 она не объявлена. Условия дальнейшего распространения следует согласовать с владельцем.

Шрифты распространяются по собственной [включённой лицензии DejaVu](plugins/eskd-electrical-cabinets/skills/eskd-electrical-cabinets/assets/fonts/LICENSE.txt). Библиотеки Python устанавливаются отдельно и сохраняют свои лицензии.

## Официальные инструкции

- [Навыки и их установка](https://learn.chatgpt.com/docs/build-skills).
- [Упаковка плагина и каталоги репозиториев](https://developers.openai.com/plugins/build/plugins).
- [Отправка плагина на рассмотрение](https://developers.openai.com/plugins/deploy/submission).

Инструкции по платформе сверены 11 октября 2026 года. Поддержка функций в конкретном клиенте и рабочей области может отличаться.

## English overview

This repository packages a Russian-language ESKD electrical and wiring drawing skill for automation cabinets. Version 0.2.0 replaces the simplified visual demo with a real frozen X2002 reference: 14 documents, 57 PDF pages, project models and five source archives. The small validation fixture is retained only to test the audit tools. The repository owner authorized publishing these materials in this public GitHub repository on October 14, 2026. Public OpenAI directory submission is pending. The skill does not program PLCs or certify electrical designs. No license has yet been selected for the authored materials; bundled fonts retain their included license.
