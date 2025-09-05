import gradio as gr
import json
from quiz_generator import generate_quiz


# -----------------------
# Quiz Logic
# -----------------------
def build_quiz_components(quiz_json: str):
    """Build quiz components from JSON string."""
    print("Parsing quiz JSON...", quiz_json)
    try:
        quiz = json.loads(quiz_json)
    except Exception:
        return [gr.Markdown("⚠️ Could not parse quiz JSON")], None

    if not quiz.get("questions"):
        return [gr.Markdown("⚠️ No questions returned by LLM")], None

    print("Populating questions...", quiz.get('questions', []))
    
    components = []
    inputs = []
    
    for i, q in enumerate(quiz.get("questions", [])):
        # Add question text
        question_text = f"**Q{i+1}: {q['question']}**"
        components.append(gr.Markdown(question_text))
        
        # Create radio buttons with A-D labels
        options_with_labels = []
        for j, option in enumerate(q["options"]):
            options_with_labels.append(f"{chr(65+j)}. {option}")
        
        radio = gr.Radio(
            choices=options_with_labels,
            label="",
            type="value"
        )
        components.append(radio)
        inputs.append(radio)
    
    return components, inputs, quiz


def grade_quiz(*user_answers, quiz=None):
    """Grade answers against quiz JSON."""
    if not quiz:
        return "⚠️ No quiz loaded."

    correct = 0
    for i, (user_answer, q) in enumerate(zip(user_answers, quiz["questions"])):
        if not user_answer:
            continue
            
        # Extract the actual answer text from the radio button selection
        # Format is "A. Answer Text", so we need to get the answer text
        try:
            # Find the correct answer in the options
            correct_answer = q["answer"]
            if user_answer.endswith(f"{correct_answer}"):
                correct += 1
        except:
            pass

    return f"Your score: {correct} / {len(quiz['questions'])}"


# -----------------------
# Gradio App
# -----------------------
with gr.Blocks() as demo:
    gr.Markdown("## 📝 Quiz Generator (gpt-oss-20B + ZeroGPU)")

    # Step 1: Prompt for quiz
    prompt_inp = gr.Textbox(label="Quiz Topic", placeholder="Capitals, Telomeres, Van Gogh")
    gen_btn = gr.Button("Generate Quiz")
    quiz_json_box = gr.Textbox(label="Raw Quiz JSON", visible=False)

    # Step 2: Quiz Container (will be populated dynamically)
    quiz_container = gr.Column()
    submit_btn = gr.Button("Submit Answers", visible=False)
    result_out = gr.Textbox(label="Result")

    state_quiz = gr.State()  # to keep parsed quiz JSON
    state_inputs = gr.State([])  # to keep input components

    def handle_generate(prompt):
        quiz_json = generate_quiz(prompt)
        components, inputs, quiz = build_quiz_components(quiz_json)
        if quiz and quiz.get("questions"):
            return quiz_json, components, gr.update(visible=True), quiz, inputs
        else:
            return quiz_json, [gr.Markdown("⚠️ No valid questions found.")], gr.update(visible=False), None, []

    def handle_submit(*user_answers):
        return grade_quiz(*user_answers, quiz=state_quiz.value)

    gen_btn.click(
        handle_generate, 
        inputs=prompt_inp, 
        outputs=[quiz_json_box, quiz_container, submit_btn, state_quiz, state_inputs]
    )

    submit_btn.click(
        handle_submit,
        inputs=state_inputs,
        outputs=result_out,
    )

demo.launch()
