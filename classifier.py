"""
MVP: синий кит классифицирует проблему с подробностями
"""
import json
import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage


# deepseek-chat поддерживает инструменты (reasoner нет)
MODEL_ID = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# пока бедолага сам формирует отчёт по багу
SYSTEM_PROMPT = (
    "You are a problem classifier agent. You receive a GitHub issue as text. "
    "Use the json_dump tool to dump json result "
    "(use it once you are sure about your problem class). "
    "JSON Fields: tags (2-5 tags as a list of strings), summary (3-5 sentences describing problem), problem_class (task specific string with 1 phrase/word)."
    "Finish as soon as you dump"
)


@tool
def json_dump(query: str) -> str:
    """Dump the json report text as a file in a directory."""
    path = "./issue_description.json"
    json_dict = json.loads(query)
    try:
        json.dump(json_dict, path, ensure_ascii=False, indent=4)
    except:
        return f"Couldn't dump - invalid JSON. Try again"
    return f"Dumped to {path}"


def main(text):
    llm = ChatDeepSeek(
        model=MODEL_ID,
        temperature=0.1,
        max_tokens=512,
        api_key="sk-cb90423eb8fe410ab35869c0b406c990"  # так лучше конечно не делать
    )
    agent = create_agent(llm, tools=[json_dump], system_prompt=SYSTEM_PROMPT)

    # issue report поступает от другого агента как json строка, но пока из json файла (агента нет)
    _ = agent.invoke({
        "messages": [
            HumanMessage(content="GitHub issue text:\n" + text)
        ]
    })


if __name__ == "__main__":
    description = """
    discount percent is calculated wrong
    """

    main(description)
