import os 

weekTranscription = os.getenv('TRANSCRIPTION')

with open(weekTranscription, "r", encoding="utf-8") as f:
    summary = f.read()

system_message = f"""
You are given a problem to solve, by using your checklist tools to plan a list of steps, then carrying out each step in turn.
Now create a plan, set the checklist, carry out the steps, and reply with the solution.
If any quantity isn't provided in the question, then include a step to come up with a reasonable estimate.
Provide your solution in Rich console markup without code blocks.
Do not ask the user questions or clarification; respond only with the answer after using your tools.
Here's a transcript of a lecture on the topic of the problem: \n{summary}\n
"""
user_message = """
Please generate 5 multiple-choice question concepts. All the questions should be relevant to the content of the lecture transcript, and be used to reinforce the key ideas.
For each question concept, generate 4 variations of the questions. Each question should have 4 answer options, and indicate which option is correct. Each of the variations should use a different answer option as the correct answer.
Each question should have one correct answer and three distractors.
The questions should be designed to test understanding of the key concepts and details presented in the lecture. 
One of the 5 questions, should be a question that requires the student to read some incomplete code, and choose the correct code to put in the gap.
"""
messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]