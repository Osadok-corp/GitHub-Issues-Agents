## ИИ-ассистент для обработки GitHub Issues


`Classifier agent (clf_agent.py)`

Функция: classify(text) — принимает текст GitHub issue, классифицирует проблему и сохраняет JSON-отчёт на диск.
Инструменты: json_dump(query) — валидирует JSON и пишет его в ./issue_description.json.
Вход/выход: текст issue → файл issue_description.json с полями tags, summary, problem_class.

`Code agent (code_agent.py)`

Функция: find_problem(issue_path) — по JSON-описанию проблемы ищет код-причину бага.
Инструменты: search_code(query) — семантический поиск по ChromaDB, возвращает топ-3 фрагмента в виде file:start-end (name) + код.
Вход/выход: issue_description.json → строка JSON с полями file, function, line range, explanation.

`Output / Report agent (output_agent.py)`

Функция: make_report(issue_path) — собирает финальный отчёт для разработчика в markdown.
Инструменты: нет — чистая генерация текста.
Вход/выход: issue_report.json (описание + code_location) → markdown-строка.


<img width="350" height="572" alt="image" src="https://github.com/user-attachments/assets/e39ef24c-4db7-4f76-a6a1-1586a3c7aac6" />
