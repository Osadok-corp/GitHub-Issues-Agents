"""
Пайплайн: URL issue -> Classifier -> Code agent -> Output agent -> текстовый отчёт

Запуск:
    python main_pipeline.py https://github.com/owner/repo/issues/123

Перед запуском репозиторий должен быть проиндексирован:
    python vector_db.py index https://github.com/owner/repo
"""
import json
import sys

from github_parsing import parse_github_issue
from classifier import main as clf_main
from agent_demo import main as agent_main
from output_agent import main as out_main

DESCRIPTION_PATH = "issue_description.json"  # сюда пишет классификатор
REPORT_PATH = "issue_report.json"            # отсюда читает output agent


def run(issue_url):
    # 1. URL -> текст issue
    text = parse_github_issue(issue_url)

    # 2. Classifier: текст -> issue_description.json (tags, summary, problem_class)
    clf_main(text)

    # 3. Code agent: описание -> где в коде баг
    location = agent_main(DESCRIPTION_PATH)

    # 4. Склеиваем описание и найденное место в один отчёт
    with open(DESCRIPTION_PATH, encoding="utf-8") as f:
        report = json.load(f)
    report["code_location"] = location
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    # 5. Output agent: отчёт -> текст для разработчика
    return out_main(REPORT_PATH)


if __name__ == "__main__":
    print(run(sys.argv[1]))