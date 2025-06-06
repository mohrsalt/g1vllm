import json
import time
from vllm import LLM, SamplingParams

# Initialize vLLM
model_name = "meta-llama/Meta-Llama-3.1-8B-Instruct"  # or your local model path
#quantization="bitsandbytes",load_format="bitsandbytes"
llm = LLM(model=model_name)
sampling_params = SamplingParams(temperature=0.2, max_tokens=800)

def make_api_call(messages, max_tokens, is_final_answer=False, custom_llm=None):
    global llm
    if custom_llm is not None:
        llm = custom_llm

    # Prepare the prompt
    prompt = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])

    for attempt in range(3):
        try:
            outputs = llm.generate([prompt], sampling_params)
            response_text = outputs[0].outputs[0].text.strip()
            if is_final_answer:
                return response_text
            else:
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Fallback: try to extract JSON substring if possible
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                    else:
                        return {"title": "Error", "content": "Response not in JSON format.", "next_action": "final_answer"}
        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return {"title": "Error", "content": f"Failed to generate final answer after 3 attempts. Error: {str(e)}"}
                else:
                    return {"title": "Error", "content": f"Failed to generate step after 3 attempts. Error: {str(e)}", "next_action": "final_answer"}
            time.sleep(1)

def generate_response(prompt, custom_llm=None):
    messages = [
        {"role": "system", "content": """You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys. USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Example of a valid JSON response:
{
"title": "Identifying Key Information",
"content": "To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...",
"next_action": "continue"
}```
"""},
{"role": "user", "content": prompt},
{"role": "assistant", "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem."}
]


    steps = []
    step_count = 1
    total_thinking_time = 0

    while True:
        start_time = time.time()
        step_data = make_api_call(messages, 300, False, custom_llm)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time

        steps.append((f"Step {step_count}: {step_data.get('title', 'Unknown')}", step_data.get('content', ''), thinking_time))

        messages.append({"role": "assistant", "content": json.dumps(step_data)})

        if step_data.get('next_action', 'final_answer') == 'final_answer' or step_count > 25:
            break

        step_count += 1

        yield steps, None

    # Generate final answer
    messages.append({"role": "user", "content": "Please provide the final answer based solely on your reasoning above. Do not use JSON formatting. Only provide the text response without any titles or preambles. Retain any formatting as instructed by the original prompt, such as exact formatting for free response or multiple choice."})

    start_time = time.time()
    final_data = make_api_call(messages, 800, True, custom_llm)
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time

    steps.append(("Final Answer", final_data, thinking_time))

    yield steps, total_thinking_time




