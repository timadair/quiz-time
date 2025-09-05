import json
import spaces
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

example_quiz = """
        {
          "questions": [
            {
              "question": "What is the capital of California?",
              "options": ["Sacramento", "Los Angeles", "San Francisco", "San Diego"],
              "answer": "Sacramento"
            },
            {
              "question": "What is the capital of France?",
              "options": ["Berlin", "Paris", "Rome", "Madrid"],
              "answer": "Paris"
            }
          ]
        }
        """

prompt = f"""
        You are a quiz writer.  You create questions and answers for multiple-choice quizzes structured in JSON.
        Each question should have four options for answers.
        One of the four answer options should be correct.      
        
        The response should formatted as JSON with a question, a list of options, and a correct answer.  
        Do not include any output after "Final Answer:" other than the quiz JSON.  Do not generate code, explanations, or markdown code blocks.
        The response must be a single valid JSON object that begins with {{ and ends with }}.  
        This is an example response of a quiz with two questions on the topic of 'capitals':
        Final Answer:{example_quiz}
    """

# Initialize model and pipeline
model_id = "openai/gpt-oss-20b"
tokenizer = AutoTokenizer.from_pretrained(model_id)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype="auto",
    device_map="auto",
)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

# -----------------------
# Hugging Face annotation for GPU inference
# 
# -----------------------
@spaces.GPU
def run_inference(prompt: str):
    return pipe(
        prompt,
        max_new_tokens=1000,
        temperature=0.7,
        do_sample=True,
    )

def generate_quiz(topic: str) -> str:
    print('topic:', topic)
    # Check for empty or null topic
    if not topic or not topic.strip():
        return '{"questions": []}'

    message = prompt + f"\nCreate a quiz with five questions and the topic {topic}."
    response = run_inference(message)
    
    # Concatenate all generated text and keep only content after the final "questions":
    all_generated = "".join(resp["generated_text"] for resp in response)
    print('all_generated:', all_generated)
    last_marker_idx = all_generated.rfind("\"questions\":")
    if last_marker_idx != -1:
        text = all_generated[last_marker_idx:].strip()
    else:
        # Fallback: use the last response's text
        text = response[-1]["generated_text"].strip()
    text = "{" + text

    print('final text:', text)
    # Try to extract JSON from the text
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        quiz_json = text[start:end]
        # Validate JSON before returning
        json.loads(quiz_json)
        return quiz_json
    except Exception:
        return '{"questions": []}'
