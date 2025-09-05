import gradio as gr
import json
from quiz_generator import generate_quiz


# -----------------------
# Quiz Logic
# -----------------------


# -----------------------
# Gradio App
# -----------------------
with gr.Blocks() as demo:
    gr.Markdown("## 📝 Quiz Generator (gpt-oss-20B + ZeroGPU)")

    # Step 1: Prompt for quiz
    prompt_inp = gr.Textbox(label="Quiz Topic", placeholder="Capitals, Telomeres, Van Gogh")
    gen_btn = gr.Button("Generate Quiz")
    quiz_json_box = gr.Textbox(label="Raw Quiz JSON", visible=False)

    # Step 2: Answer inputs (fixed number of radio buttons with inline questions)
    with gr.Row():
        q1_radio = gr.Radio(choices=[], label="", visible=False)
        q2_radio = gr.Radio(choices=[], label="", visible=False)
    with gr.Row():
        q3_radio = gr.Radio(choices=[], label="", visible=False)
        q4_radio = gr.Radio(choices=[], label="", visible=False)
    with gr.Row():
        q5_radio = gr.Radio(choices=[], label="", visible=False)
    
    submit_btn = gr.Button("Submit Answers", visible=False)
    result_out = gr.Textbox(label="Result")

    state_quiz = gr.State()  # to keep parsed quiz JSON

    def handle_generate(prompt):
        quiz_json = generate_quiz(prompt)
        try:
            quiz = json.loads(quiz_json)
        except:
            return quiz_json, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), None

        if not quiz.get("questions"):
            return quiz_json, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), None

        # Update radio buttons for each question with inline question text
        updates = [quiz_json, gr.update(visible=True)]
        
        # Update radio button choices for each question
        radio_buttons = [q1_radio, q2_radio, q3_radio, q4_radio, q5_radio]
        for i, q in enumerate(quiz.get("questions", [])):
            if i < len(radio_buttons):
                options_with_labels = [f"{chr(65+j)}. {option}" for j, option in enumerate(q["options"])]
                question_label = f"Q{i+1}: {q['question']}"
                updates.append(gr.update(choices=options_with_labels, label=question_label, visible=True))
            else:
                updates.append(gr.update(visible=False))
        
        # Fill remaining radio buttons as invisible
        for i in range(len(quiz.get("questions", [])), len(radio_buttons)):
            updates.append(gr.update(visible=False))
        
        updates.append(quiz)
        return updates

    def handle_submit(q1, q2, q3, q4, q5, quiz):
        if not quiz:
            return "⚠️ No quiz loaded."
        
        answers = [q1, q2, q3, q4, q5]
        correct = 0
        
        for i, (user_answer, q) in enumerate(zip(answers, quiz["questions"])):
            if not user_answer:
                continue
            try:
                correct_answer = q["answer"]
                if user_answer.endswith(f"{correct_answer}"):
                    correct += 1
            except:
                pass

        return f"Your score: {correct} / {len(quiz['questions'])}"

    gen_btn.click(
        handle_generate, 
        inputs=prompt_inp, 
        outputs=[quiz_json_box, submit_btn, q1_radio, q2_radio, q3_radio, q4_radio, q5_radio, state_quiz]
    )

    submit_btn.click(
        handle_submit,
        inputs=[q1_radio, q2_radio, q3_radio, q4_radio, q5_radio, state_quiz],
        outputs=result_out,
    )

demo.launch()
