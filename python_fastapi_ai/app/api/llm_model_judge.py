import os
import json
from dotenv import load_dotenv
from openai import OpenAI



load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
request += "Answer only with the question, no explanation."
messages = [{"role": "user", "content": request}]

print("message for a question:", messages)

openai = OpenAI(api_key=openai_api_key)
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
)
question = response.choices[0].message.content

print("question:", question)

competitors = []
answers = []
messages = [{"role": "user", "content": question}]


# GPT 5 Nano Answer for the question
model_name = "gpt-5-nano"
response = openai.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content
print("GPT 5 Nano Response:", answer)
competitors.append(model_name)
answers.append(answer)


#Gemini 2.5 Flash Answer for the question
gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
model_name = "gemini-2.5-flash"
response = gemini.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content
print("Gemini 2.5 Flash Response:", answer)
competitors.append(model_name)
answers.append(answer)


print(competitors)
print(answers)

together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index+1}\n\n"
    together += answer + "\n\n"

print(together)

# Save the results to a JSON file
with open("results.json", "w") as f:
    json.dump({"competitors": competitors, "answers": answers}, f)

judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

print(judge)
judge_messages = [{"role": "user", "content": judge}]

openai = OpenAI()
response = openai.chat.completions.create(
    model="gpt-5-mini",
    messages=judge_messages,
)
results = response.choices[0].message.content
print(results)

print("Judge Results:", results)

results_dict = json.loads(results)
ranks = results_dict["results"]

for index, result in enumerate(ranks):
    competitor = competitors[int(result) - 1]
    print(f"Rank {index + 1}: {competitor}")




