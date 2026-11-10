"""
MVP: синий кит ловит баги

Запуск: pip install -r requirements.txt
"""
import json
import sys

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek

from vector_db import search

# deepseek-chat поддерживает инструменты (reasoner нет)
MODEL_ID = "deepseek-chat"

SYSTEM_PROMPT = """
<task>
You are a programming agent. You receive a GitHub issue as JSON.
Use the search_code tool to find the code that causes the problem
(you may call it several times with different queries).
</task>

<input>
A JSON object describing a GitHub issue.
</input>

<constraints>
1. Use the search_code tool to locate the relevant code; you may call it
   several times with different queries.
2. Do not invent file paths, function names, line ranges, or explanations
   that are not supported by the search results.
3. Answer as a JSON string with the fields 'file', 'function',
   'line range', and 'explanation'.
4. 'explanation' must be a one-sentence description of what caused the
   problem.
5. Keep the tone dry and professional.
</constraints>

<success>
A valid JSON string with the fields 'file', 'function', 'line range',
and 'explanation', grounded in the search results.
</success>
"""


@tool
def search_code(query: str) -> str:
    """Search the repository's source code by meaning. Returns the most relevant functions."""
    print("Search the database...")
    parts = []
    for hit in search(query, n_results=3):
        parts.append(f"{hit['file']}:{hit['start_line']}-{hit['end_line']} ({hit['name']})\n{hit['code']}")
    return "\n\n---\n\n".join(parts)


def find_problem(issue_path):
    print("Looking through code...")
    with open(issue_path, encoding="utf-8") as f:
        issue = json.load(f)

    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="..."  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[search_code], system_prompt=SYSTEM_PROMPT)

    # issue report поступает от другого агента как json строка, но пока из json файла (агента нет)
    result = agent.invoke({"messages": [
        {"role": "user", "content": "GitHub issue:\n" + json.dumps(issue, indent=2)}
    ]})
    print("Got the issue!")
    return result["messages"][-1].content


if __name__ == "__main__":
    find_problem(sys.argv[1] if len(sys.argv) > 1 else "sample_issue.json")
