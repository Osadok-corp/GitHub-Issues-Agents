"""
MVP: синий кит классифицирует проблему с подробностями
"""
import json

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage


# deepseek-chat поддерживает инструменты (reasoner нет)
MODEL_ID = "deepseek-chat"

SYSTEM_PROMPT = """
<task>
You are the Problem Classifier agent in a GitHub-issue analysis pipeline.
You receive a GitHub issue as text and produce a classification report
for the problem it describes.
</task>

<input>
The GitHub issue text.
</input>

<constraints>
1. Classify the problem described in the issue.
2. Dump the classification result as JSON using the json_dump tool.
   Call it once you are sure about the problem class.
3. The JSON must contain the following fields:
   - 'tags': 2-5 tags as a list of strings.
   - 'summary': 3-5 sentences describing the problem.
   - 'problem_class': task-specific string with 1 phrase/word.
4. Do not invent details that are not present in the issue text.
5. Keep the tone dry and professional.
6. Finish as soon as you have dumped the JSON.
</constraints>

<success>
A valid JSON dumped via json_dump containing the fields 'tags',
'summary' and 'problem_class', grounded in the issue text.
</success>
"""


@tool
def json_dump(query: str) -> str:
    """Dump the json report text as a file in a directory."""
    print("Creating a JSON...")
    path = "./issue_description.json"
    json_dict = json.loads(query)
    try:
        with open(path, "w", encoding="utf-8") as f:
            print("JSON created!")
            json.dump(json_dict, f, ensure_ascii=False, indent=4)
    except Exception:
        print("JSON creation failed...")
        return "Couldn't dump - invalid JSON. Try again"
    return f"Dumped to {path}"


def classify(text):
    print("Classifying Problem...")
    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="..."  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[json_dump], system_prompt=SYSTEM_PROMPT)

    # issue report поступает от другого агента как json строка, но пока из json файла (агента нет)
    _ = agent.invoke({
        "messages": [
            HumanMessage(content="GitHub issue text:\n" + text)
        ]
    })
    print("Problem Classified. Passing to Code agent...")


if __name__ == "__main__":
    description = """
    discount percent is calculated wrong
    """
    classify(description)
