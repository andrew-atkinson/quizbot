"""Prompt construction.

Pure: build_messages() takes a transcript (and optional course/week metadata) and returns
the chat messages. No file or env I/O at import — the caller (pipeline.py) reads the file and
supplies the metadata. This is what lets one process handle many weeks of many courses.
"""

# The transcript sits above the closing rules rather than at the end. A small model attends
# to the end of the prompt, and the commit rule is what must land.
_SYSTEM_TEMPLATE = """
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
{context_line}
Lecture transcript:
<transcript>
{transcript}
</transcript>

After finalize_bank succeeds, reply with one short plain sentence and stop.
Do not ask the user questions. Do not use Rich markup or code blocks in your replies.

Remember: a tool call is the only thing that counts. Prose is discarded. To revise, call
the same tool again with the same group_id and variant_label.
"""

USER_MESSAGE = """
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


def _context_line(course_title, week_label, module) -> str:
    """A single factual line placing the lecture, or '' when nothing is known.

    Kept plain and unambiguous rather than fluent — it is orienting metadata for the model,
    not prose it should imitate.
    """
    parts = []
    if week_label:
        parts.append(week_label)
    if module:
        parts.append(module)
    if course_title:
        parts.append(f"course: {course_title}")
    if not parts:
        return ""
    return "\nLecture context — " + "; ".join(parts) + ".\n"


def build_messages(transcript: str, *, course_title: str | None = None,
                   week_label: str | None = None, module: str | None = None) -> list[dict]:
    """The chat messages for one lecture. Metadata is woven in only when supplied."""
    system_message = _SYSTEM_TEMPLATE.format(
        context_line=_context_line(course_title, week_label, module),
        transcript=transcript,
    )
    return [{"role": "system", "content": system_message},
            {"role": "user", "content": USER_MESSAGE}]
