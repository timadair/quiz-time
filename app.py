import gradio as gr
import json
from quiz_generator import generate_quiz


# -----------------------
# Quiz Logic
# -----------------------
def build_quiz_ui(quiz_json: str):
    """Build quiz UI dynamically from JSON string."""
    try:
        quiz = json.loads(quiz_json)
    except Exception:
        return [gr.Markdown("⚠️ Could not parse quiz JSON")], None

    inputs = []
    components = []

    with gr.Column() as col:
        for i, q in enumerate(quiz.get("questions", [])):
            components.append(gr.Markdown(f"**Q{i+1}: {q['question']}**"))
            inp = gr.Radio(choices=q["options"], label="", type="value")
            inputs.append(inp)
    return col, inputs, quiz


def grade_quiz(*user_answers, quiz=None):
    """Grade answers against quiz JSON."""
    if not quiz:
        return "⚠️ No quiz loaded."

    correct = 0
    for ans, q in zip(user_answers, quiz["questions"]):
        if ans == q["answer"]:
            correct += 1
    return f"Your score: {correct} / {len(quiz['questions'])}"


# -----------------------
# Gradio App
# -----------------------
with gr.Blocks() as demo:
    gr.Markdown("## 📝 Quiz Generator (gpt-oss-20B + ZeroGPU)")

    # Step 1: Prompt for quiz
    prompt_inp = gr.Textbox(label="Quiz Topic", placeholder="Capitals, Telomeres, Van Gogh")
    gen_btn = gr.Button("Generate Quiz")
    quiz_json_box = gr.Textbox(label="Raw Quiz JSON")

    # Step 2: Quiz UI (dynamic)
    quiz_container = gr.Column()
    submit_btn = gr.Button("Submit Answers", visible=False)
    result_out = gr.Textbox(label="Result")

    state_quiz = gr.State()  # to keep parsed quiz JSON

    def handle_generate(prompt):
        return generate_quiz(prompt)

    def handle_build(quiz_json):
        col, inputs, quiz = build_quiz_ui(quiz_json)
        if quiz and quiz.get("questions"):
            return col, gr.update(visible=True), quiz
        else:
            return [gr.Markdown("⚠️ No valid questions found.")], gr.update(visible=False), None

    gen_btn.click(handle_generate, inputs=prompt_inp, outputs=quiz_json_box)
    quiz_json_box.change(
        handle_build,
        inputs=quiz_json_box,
        outputs=[quiz_container, submit_btn, state_quiz],
    )

    submit_btn.click(
        fn=grade_quiz,
        inputs=[],
        outputs=result_out,
        preprocess=False,
        postprocess=False,
    )
demo.launch()
