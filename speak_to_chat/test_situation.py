import os
import openai
from dotenv import load_dotenv
load_dotenv()

load_dotenv()
openai.api_key = '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'

# 미리 n개의 질문을 생성한 후 질문을 나누어 사용자에게 전달
def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

selector_name = "금융"
career = "신입"
job_name = "경영"
messages =  [  
{"role": "system","content": f"""From now on, you are acting as a job interviewer. Create 10 different questions '\' for applicants who applied for {selector_name} as {career} and {job_name} about the possible situations of working as {job_name}. Make sure to create questions in Korean."""}]
response = get_completion_from_messages(messages, temperature=0.7)
print(response)