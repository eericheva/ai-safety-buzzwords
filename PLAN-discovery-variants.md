# План: discovery + расширение VARIANTS (и роль OpenAlex)

Дата: 2026-07-18

## Принятое решение

**Не** переводить основной сбор счётчиков на OpenAlex-keywords/topics.
Primary-источник остаётся: полнотекстовый phrase-match по `title+abstract`
(`collect.py`, S2) с word-boundary верификацией. OpenAlex используется только
как **вторичный** сигнал — для discovery и QA, не для метрик.

Причина коротко: OpenAlex keywords/topics — это алгоритмические теги, а проект
меряет реальное словоупотребление авторов. Теги грубее по гранулярности
(схлопывают близкие концепты), запаздывают по датам для свежих терминов и не
покрывают все баззворды. Подробности — в переписке; здесь только план работ.

Приоритет: **(1) discovery-дожать → (2) semantic VARIANTS-expansion → (3) cross-val**.

---

## (1) Discovery-дожать — 30 мин, чистый плюс, нулевой риск для метрик

Конвейер уже есть: `discover.py --source openalex` тянет `keywords`/`topics`,
фильтрует через `novelty_filter()` и пишет `data/openalex_keywords.csv`
(`discover.py:113` `discover_openalex`).

Что докрутить:

1. **Прогнать все три источника и свести в один ranked-лист кандидатов.**
   ```bash
   python discover.py --source openalex --query "AI safety large language model" --year-from 2019 --pages 20
   python discover.py --source raw2
   python discover.py --source mit
   ```
   Сейчас каждый пишет свой CSV. Добавить маленький свод `discover_merge()`:
   объединить `openalex_keywords.csv` + `raw2` + `mit` в
   `data/discovery_candidates.csv` с колонкой `sources` (в скольких источниках
   встретился термин — кандидаты из ≥2 источников идут вверх).

2. **Триаж-петля.** Верх списка глазами → отобранные термины дописать в
   `BUZZWORDS` + при необходимости `VARIANTS` в `buzzwords.py`. Это ручной шаг,
   но список уже отфильтрован `novelty_filter()`, так что дёшево.

3. **Гигиена.** Вынести `mailto` OpenAlex в переменную окружения (сейчас через
   `--mailto`), чтобы попадать в polite pool и не ловить троттлинг.

Критерий готовности: единый `data/discovery_candidates.csv`, из него добавлено
N новых баззвордов в глоссарий.

---

## (2) Semantic VARIANTS-expansion — реальная дыра, которую стоит закрыть

Проблема: синонимы ловятся только если руками прописаны в `VARIANTS`
(`buzzwords.py:192`). Статья с непрописанным синонимом молча пропускается →
занижение счётчиков. Это главная методологическая слабость сейчас.

У нас **уже есть** нужная инфраструктура: `data/embeddings.npz` — SPECTER2
(768-d) векторы по статьям, из `groupings_embed.py`. Значит эмбеддинги бесплатны.

План (новый скрипт `variants_suggest.py`):

1. Для каждого баззворда взять его текущий центроид (mean SPECTER2 его статей —
   ровно как в `groupings_embed.py` `fetch_embeddings`/агрегация).
2. Кандидаты-синонимы берём НЕ из воздуха, а из уже собранного корпуса:
   n-граммы (1–3 слова) из `title+abstract` статей раздела `data/raw2/`,
   отфильтрованные `STOP` (список уже есть в `discover.py`).
3. Эмбеддить кандидат-фразы (тем же S2 SPECTER2 endpoint, что в
   `groupings_embed.py`) и ранжировать по cosine к центроиду баззворда.
4. Вывести `data/variants_suggestions.csv`: `term, candidate, cosine,
   sample_paper`. Верх списка — на ручное одобрение в `VARIANTS`.

Важно: это **suggestion-tool, не авто-инжект.** Порог cosine + человек в петле,
иначе затащим ложные синонимы и раздуем счётчики (та же ошибка, что и слепой
OpenAlex-keywords). Одобренные формы дописываем в `VARIANTS` руками.

Проверка эффекта: после добавления форм перегнать `collect.py` по затронутым
баззвордам и сравнить `verified_arxiv` до/после — рост = пойманные синонимы.

Критерий готовности: `variants_suggestions.csv` + ≥1 баззворд с доказанным
приростом verified-count после добавления одобренного синонима.

---

## (3) Cross-source validation через OpenAlex — nice-to-have, QA-only

Идея: для баззвордов, у которых **есть** свой OpenAlex topic ID, тянуть
`works?filter=topics.id:T...` как независимый счётчик и сверять с нашим
verified-count. Расхождение = сигнал: либо дыра в `VARIANTS`, либо термин
шире/уже, чем мы думали.

План (новый скрипт `crossval_openalex.py`):

1. Резолв topic ID: `GET api.openalex.org/topics?search=<term>` → взять топ-1
   если `display_name` достаточно близок (иначе пометить «нет topic», это норма).
2. Для сматченных — `works?filter=topics.id:T...,from_publication_date:...` →
   `meta.count`.
3. Отчёт `data/crossval.csv`: `term, our_verified, openalex_topic_count, ratio,
   topic_name`. Сортировать по |log(ratio)| — верх = самые подозрительные.

Жёсткое правило: **openalex_topic_count НЕ подмешивается в основной счётчик.**
Только диагностика — куда посмотреть человеку. Результаты (найденные дыры)
возвращаются в задачу (2) как список терминов для доработки VARIANTS.

Критерий готовности: `crossval.csv`, из него выявлено ≥1 реальное расхождение,
объяснённое дырой в VARIANTS или уточнением scope.

---

## Что НЕ делаем

- Сбор счётчиков по OpenAlex keywords/topics как primary-источник — нет.
- Авто-инжект синонимов без ручного одобрения — нет (риск раздуть метрики).
- Замена S2 phrase-match — нет; он остаётся эталоном словоупотребления.

## Файлы, которые появятся/изменятся

- изм. `discover.py` — добавить `discover_merge()`, env-var для mailto
- нов. `data/discovery_candidates.csv` — свод кандидатов
- нов. `variants_suggest.py` + `data/variants_suggestions.csv`
- изм. `buzzwords.py` — руками одобренные термины/формы в `BUZZWORDS`/`VARIANTS`
- нов. `crossval_openalex.py` + `data/crossval.csv`
