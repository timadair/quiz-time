import gradio as gr
import json

quiz_json = """
{
  "questions": [
    {
      "question": "What is 2 + 2?",
      "options": ["3", "4", "5", "22"],
      "answer": "4"
    },
    {
      "question": "Capital of France?",
      "options": ["Berlin", "Paris", "Rome", "Madrid"],
      "answer": "Paris"
    }
  ]
}
"""

quiz = json.loads(quiz_json)

def grade(*user_answers):
    correct = 0
    for ans, q in zip(user_answers, quiz["questions"]):
        if ans == q["answer"]:
            correct += 1
    return f"Your score: {correct} / {len(quiz['questions'])}"

with gr.Blocks() as demo:
    inputs = []
    with gr.Column():
        for i, q in enumerate(quiz["questions"]):
            gr.Markdown(f"**Q{i+1}: {q['question']}**")
            inp = gr.Radio(choices=q["options"], label="", type="value")
            inputs.append(inp)
    submit = gr.Button("Submit")
    result = gr.Textbox(label="Result")
    submit.click(fn=grade, inputs=inputs, outputs=result)

demo.launch()