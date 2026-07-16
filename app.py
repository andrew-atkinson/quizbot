import os
from datetime import datetime
from rich.console import Console
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv(override=True)

from context import messages
from tools import tools, handle_tool_calls, show

MODEL_NAME = os.getenv("MODEL_NAME")
LOCAL_HOST_URL = os.getenv("LOCAL_HOST_URL")
lmstudio = OpenAI(base_url=LOCAL_HOST_URL, api_key='lmstudio')


def loop(messages):
    response = lmstudio.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = lmstudio.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    show(response.choices[0].message.content)
    return response.choices[0].message.content

if __name__ == "__main__":
    checklist, completed = [], []
    raw_quiz_info = loop(messages)
    
    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"quiz_{timestamp}.txt")
    
    # Save the content to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(raw_quiz_info)
    
    print(f"Quiz info saved to {filename}")
