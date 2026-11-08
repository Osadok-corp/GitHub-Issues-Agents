"""
Пайплайн: URL issue -> Classifier -> Code agent -> Output agent -> текстовый отчёт

Запуск: python main_pipeline.py [issue_url]
(Перед запуском репозиторий должен быть проиндексирован)
python vector_db.py index [repo_url]
"""
import json
import sys

from github_parsing import parse_github_issue
from clf_agent import classify
from code_agent import find_problem
from output_agent import make_report

DESCRIPTION_PATH = "issue_description.json"  # сюда пишет классификатор
REPORT_PATH = "issue_report.json"            # отсюда читает output agent


def run(issue_url):
    # 1.URL -> текст issue
    text = parse_github_issue(issue_url)
    # 2.clf_agent: текст -> issue_description.json
    classify(text)
    # 3.code_agent: описание -> json строка по багу
    location = find_problem(DESCRIPTION_PATH)

    # 4.склеиваем описание и найденное место в один JSON
    with open(DESCRIPTION_PATH, encoding="utf-8") as f:
        report = json.load(f)
    report["code_location"] = location
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    # 5.output_agent: отчёт -> текст для разработчика
    print(make_report(REPORT_PATH))


if __name__ == "__main__":
    print(run(sys.argv[1]))