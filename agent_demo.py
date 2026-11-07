"""
MVP: синий кит ловит баги

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
    "You are a programming agent. You receive a GitHub issue as JSON. "
    "Use the search_code tool to find the code that causes the problem "
    "(you may call it several times with different queries). "
    "Then answer with: the file, the function, the line range, and a one-sentence explanation as JSON string"
    "JSON fields: 'file', 'function', 'line range'"
)


@tool
def search_code(query: str) -> str:
    """Search the repository's source code by meaning. Returns the most relevant functions."""
    parts = []
    for hit in search(query, n_results=3):
        parts.append(f"{hit['file']}:{hit['start_line']}-{hit['end_line']} ({hit['name']})\n{hit['code']}")
    return "\n\n---\n\n".join(parts)


def main(issue_path):
    with open(issue_path, encoding="utf-8") as f:
        issue = json.load(f)

    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="sk-cb90423eb8fe410ab35869c0b406c990"  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[search_code], system_prompt=SYSTEM_PROMPT)

    # issue report поступает от другого агента как json строка, но пока из json файла (агента нет)
    result = agent.invoke({"messages": [
        {"role": "user", "content": "GitHub issue:\n" + json.dumps(issue, indent=2)}
    ]})

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample_issue.json")
