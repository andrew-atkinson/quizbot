import os
from pathlib import Path

weekTranscription = os.getenv('TRANSCRIPTION')

with open(weekTranscription, "r", encoding="utf-8") as f:
    summary = f.read()

source_name = Path(weekTranscription).name

# The transcript sits above the closing rules rather than at the end. A small model
# attends to the end of the prompt, and the commit rule is what must land.
system_message = f"""
You write assessment items for a university course and record them using tools.

THE ONLY WAY TO RECORD A QUESTION IS A TOOL CALL.
Text in your reply is thrown away. Never write a question, an option, or a correction as prose.

To fix a mistake, call the same add_ tool again with the same group_id and variant_label.
That REPLACES the earlier version completely. Do not announce corrections, do not restart,
do not write things like "(wait, this is the same as A)". Just call the tool again.
Re-calling is free and leaves no trace of the old version.

Work in this order:
1. create_checklist       - one item per concept you plan to write.
2. create_question_group  - once per concept, before any of its variants.
3. add_<type>_variant     - once per FINISHED variant, four per group, labels A, B, C, D.
                            Each reply tells you what is still missing. Read it.
4. mark_complete          - once a group's four variants are all recorded.
5. get_bank_report        - once, when you believe you are done.
6. finalize_bank          - last. If it reports problems, fix them with more add_ calls
                            and call it again.

Content rules:
- Every question must be answerable from the lecture transcript below.
- Put code in Markdown backticks and set text_format="markdown" for that variant.
  Code left outside backticks will not render correctly.
- Options must differ from one another in meaning, not just in wording.

Lecture transcript:
<transcript>
{summary}
</transcript>

After finalize_bank succeeds, reply with one short plain sentence and stop.
Do not ask the user questions. Do not use Rich markup or code blocks in your replies.

Remember: a tool call is the only thing that counts. Prose is discarded. To revise, call
the same tool again with the same group_id and variant_label.
"""

user_message = """
Build a question bank for this lecture.

Five concepts, one question group each:
- c1 to c4: the four most important ideas in the transcript.
- c5: a code-completion question. The student reads code with a gap and picks the code that
  belongs in the gap. Use question_type="multiple_choice" and text_format="markdown".

Types: at least three of the five groups must be "multiple_choice". You may use "multiple_answer",
"true_false", "short_answer", "numerical" or "matching" for the others where the concept genuinely
suits it. Do not pick a type just for variety.

Use "multiple_answer" only when a concept really has several correct answers at once, so the
student must pick every one of them. If exactly one answer is right, it is "multiple_choice".
The marks are worked out for you: just say which options are correct.

Four variants per group, labelled A, B, C, D. Each variant is a DIFFERENT question testing the
same concept, not a reworded copy of the same question.

Every variant needs a variant_summary: a few words naming the angle THAT variant takes, which
becomes its name in the question bank. Within a group they must all differ. For a concept like
"Anatomy of a for loop" the four summaries might be "Purpose of the condition", "What the
incrementer does", "Role of initialization" and "Loop syntax". Write the summary first: if you
cannot say how a variant differs from the other three in a few words, it is too similar and you
should write a different question.

For multiple_choice variants: exactly four options, one correct and three plausible distractors
drawn from mistakes a student would really make. Across a group's four variants the correct
option must sit at index 0 in one, 1 in another, 2 in another and 3 in the last. The tool reply
tells you which positions are still free.

For true_false groups: at least one variant must be true and at least one must be false.

Start by calling create_checklist.
"""

messages = [{"role": "system", "content": system_message},
            {"role": "user", "content": user_message}]
