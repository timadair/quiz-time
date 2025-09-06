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

system_prompt = f"""
        You are a quiz writer.  You create questions and answers for multiple-choice quizzes structured in JSON.
        Each question should have four options for answers.
        One of the four answer options should be correct. 
        Reasoning: low     
        
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

@spaces.GPU(duration=45)
def run_inference(prompt_messages):
    """
    @spaces.GPU is a Hugging Face decorator for GPU inference.
    Required for the ZeroGPU setting in HF Spaces.
    duration is the expected duration of the inference.  duration=45 allows visitors with up to 45s of remaining ZeroGPU inference time for the day to use the space.
    See https://huggingface.co/docs/hub/en/spaces-zerogpu

    :param prompt_messages: The system and user messages submitted to the LLM
    :return: All messages returned by the LLM
    """
    return pipe(
        prompt_messages,
        max_new_tokens=1500,
        temperature=0.7,
        do_sample=True,
    )

def to_final_answer(response):
    """
    Isolates the JSON of the final answer in the LLMs response.
    May not be true: There's not a token that gpt-oss-20b returns reliably enough to indicate it's done,
    so the best bet is to find the last instance of the first key in the JSON and add the starting '{' back on.

    Shouldn't be necessary if I change to using a LlamaIndex agent to enable tool use.

    Final correction: 
    gpt-oss-20b has used the token "assistantfinal" pretty consistently today.  I also see it come up in web searches.  
    It might be a good stop token if it continues.
    """
    first_json_key = '"questions":'

    # Code from https://huggingface.co/docs/transformers/en/conversations#textgenerationpipeline
    # The assistant response is always the last in the generated_text array, so -1.
    assistant_response = response[0]["generated_text"][-1]["content"]

    print('all_generated:', assistant_response)
    last_marker_idx = assistant_response.rfind(first_json_key)
    if last_marker_idx != -1:
        text = "{" + assistant_response[last_marker_idx:].strip()
    else:
        # Fallback: use the last response's text
        text = response[-1]["generated_text"].strip()
    print('final text:', text)
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
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create a quiz with five questions and the topic {topic}.  Your final answer must be a parseable JSON object."},
    ]

    response = run_inference(messages)
    text = to_final_answer(response)

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
