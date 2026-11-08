"""
Вход: путь к JSON репорту по проблеме
Выход: строка в markdown с репортом для разработчика
"""
import json
import sys

from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek


# deepseek-chat поддерживает инструменты (reasoner нет)
MODEL_ID = "deepseek-chat"

SYSTEM_PROMPT = """
<task>
You are the Report Generator in a GitHub-issue analysis pipeline.
You receive the outputs of the previous stages and produce a final report for a developer.
</task>

<input>
A JSON object with three blocks:
-  'file': file path where the problem is located.
- 'function': function or method where problem is.
- 'line range': line range where the problem is.
- 'explanation': brief explanation of what went wrong.
</input>

<constraints>
1. Return readable clean markdown text.
2. Do not invent details that are not present in the input blocks.
   If information is missing, state this in "potential_problem" instead of guessing.
3. Keep the tone dry and professional. Do not paraphrase the input.
</constraints>

<success>
A valid markdown text, clean structure, professional tone,
</success>
"""


def make_report(issue_path):
    # читаем json с issue
    with open(issue_path, encoding="utf-8") as f:
        issue = json.loads(f.read())

    print("Loaded Issue. Working on report...")

    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="sk-cb90423eb8fe410ab35869c0b406c990"  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[], system_prompt=SYSTEM_PROMPT)
    msg_text = "GitHub issue:\n" + json.dumps(issue, indent=2)

    result = agent.invoke({"messages": [
        {"role": "user", "content": msg_text}
    ]})

    print("REPORT FOR THE DEVELOPER:")
    return result["messages"][-1].content


if __name__ == "__main__":
    # если аргумент не передали — берём файл по умолчанию
    if len(sys.argv) > 1:
        p = sys.argv[1]
    else:
        p = "issue_report.json"