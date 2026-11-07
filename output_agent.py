"""
MVP: синий кит говорит

Запуск: pip install -r requirements.txt
"""
import json
import os
import sys

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek


from vector_db import search

# deepseek-chat поддерживает инструменты (reasoner нет)
MODEL_ID = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# пока бедолага сам формирует отчёт по багу
SYSTEM_PROMPT = (
    "You are a report wrtier agent. You receive a GitHub issue report as JSON. "
    "Answer professionally, don't overword, provide a dry analysis for a developer with solution instructions."
)


def main(issue_path):
    with open(issue_path, encoding="utf-8") as f:
        issue = json.load(f)

    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="sk-cb90423eb8fe410ab35869c0b406c990"  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[], system_prompt=SYSTEM_PROMPT)

    # issue report поступает от другого агента как json строка, но пока из json файла (агента нет)
    result = agent.invoke({"messages": [
        {"role": "user", "content": "GitHub issue:\n" + json.dumps(issue, indent=2)}
    ]})

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "issue_report.json")