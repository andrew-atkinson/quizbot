import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from dotenv import load_dotenv
load_dotenv(override=True)

import bank
from context import messages, source_name
from tools import handle_tool_calls, set_call_log, show, tools

MODEL_NAME = os.getenv("MODEL_NAME")
LOCAL_HOST_URL = os.getenv("LOCAL_HOST_URL")
lmstudio = OpenAI(base_url=LOCAL_HOST_URL, api_key='lmstudio')


def loop(messages, max_iters: int = 50):
    """Run until the bank is finalized, the model stops, or we run out of turns.

    max_iters matters more than it used to: a variant can now be revised for free, so a
    model that keeps 'improving' variant A has no reason of its own to stop.
    """
    choice = None
    for _ in range(max_iters):
        response = lmstudio.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools
        )
        choice = response.choices[0]
        if choice.finish_reason != "tool_calls":
            break
        messages.append(choice.message)
        messages.extend(handle_tool_calls(choice.message.tool_calls))
        if bank.is_finalized():
            break
    else:
        show(f"[yellow]Stopped after {max_iters} turns without finalizing.[/yellow]")

    # LM Studio returns content=None after a tool-heavy run, and f.write(None) is a TypeError.
    return (choice.message.content or "") if choice else ""


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("output") / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    bank.init(run_id=timestamp, out_dir=run_dir,
              title=f"Quiz bank {timestamp}", source=source_name)
    set_call_log(run_dir / "calls.jsonl")

    reply = loop(messages)

    # The transcript is now a debugging aid, not the deliverable: finalize_bank writes
    # bank.json / quiz.json / bank.gift / quiz_<seed>.gift as the model works.
    (run_dir / "reply.txt").write_text(reply, encoding="utf-8")

    if not bank.is_finalized():
        problems = bank.validate_final()
        show("[red]Bank was not finalized.[/red] Partial work is still in bank.json.")
        for p in problems:
            show(f"  - {p}")
    show(f"Run artifacts in {run_dir}")
