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

@spaces.GPU(duration=120)
def run_inference(prompt_message: str):
    """
    @spaces.GPU is a Hugging Face decorator for GPU inference.
    Required for the ZeroGPU setting in HF Spaces.
    duration=300 allows visitors to use up to 300s of inference.
    See https://huggingface.co/docs/hub/en/spaces-zerogpu

    :param prompt_message: The user message submitted to the LLM
    :return: All messages returned by the LLM
    """
    return pipe(
        prompt_message,
        max_new_tokens=1000,
        temperature=0.7,
        do_sample=True,
    )

def to_final_answer(response):
    """
    Isolates the JSON of the final answer in the LLMs response.
    There's not a token that gpt-oss-20b returns reliably enough to indicate it's done,
    so the best bet is to find the last instance of the first key in the JSON and add the starting '{' back on.

    Shouldn't be necessary if I change to using a LlamaIndex agent to enable tool use.
    """
    first_json_key = '"questions":'

    # Concatenate all generated text and keep only content after the final "questions":
    all_generated = "".join(resp["generated_text"] for resp in response)
    print('all_generated:', all_generated)
    last_marker_idx = all_generated.rfind(first_json_key)
    if last_marker_idx != -1:
        text = "{" + all_generated[last_marker_idx:].strip()
    else:
        # Fallback: use the last response's text
        text = response[-1]["generated_text"].strip()
    return text


def generate_quiz(topic: str) -> str:
    f"""
    Synchronously generates a multiple-choice quiz with 5 questions from the given topic using LLM inference.
    Rather slow since the gpt-oss-20B does a lot of thinking.
    TODO Possible enhancement: return a LlamaIndex Handler if the user wants to see CoT happening real-time.
    :param topic: The topic of the quiz
    :return: JSON in the format of {example_quiz}
    """
    print('topic:', topic)
    if not topic or not topic.strip():
        return '{"Inference not run": "No valid topic"}'

    message = prompt + f"\nCreate a quiz with five questions and the topic {topic}."
    response = run_inference(message)

    text = to_final_answer(response)

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
        return "Could not extract a complete JSON object.  Try again!"
