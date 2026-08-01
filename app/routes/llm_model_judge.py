import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/fastapi/llm/model_judge")
def llm_model_judge_question():
    """Generate a question, collect LLM answers, and rank them with a judge model."""
    try:
        load_dotenv(override=True)

        openai_api_key = os.getenv("OPENAI_API_KEY")

        request = (
            "Please come up with a challenging, nuanced question that I can ask a number of LLMs "
            "to evaluate their intelligence. "
        )
        request += "Answer only with the question, no explanation."
        messages = [{"role": "user", "content": request}]

        openai_client = OpenAI(api_key=openai_api_key)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        question = response.choices[0].message.content

        competitors = []
        answers = []
        messages = [{"role": "user", "content": question}]

        model_name = "gpt-5-nano"
        response = openai_client.chat.completions.create(model=model_name, messages=messages)
        answer = response.choices[0].message.content
        competitors.append(model_name)
        answers.append(answer)

        model_name = "gpt-5-mini"
        response = openai_client.chat.completions.create(model=model_name, messages=messages)
        answer = response.choices[0].message.content
        competitors.append(model_name)
        answers.append(answer)

        together = ""
        for index, answer in enumerate(answers):
            together += f"# Response from competitor {index + 1}\n\n"
            together += answer + "\n\n"

        judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

        judge_messages = [{"role": "user", "content": judge}]
        print("judge_messages:", judge_messages)
        judge_client = OpenAI(api_key=openai_api_key)
        response = judge_client.chat.completions.create(
            model="gpt-5-mini",
            messages=judge_messages,
        )
        results = response.choices[0].message.content

        results_dict = json.loads(results)
        ranks = results_dict["results"]

        rankings = []
        for index, result in enumerate(ranks):
            competitor = competitors[int(result) - 1]
            rankings.append({"rank": index + 1, "competitor": competitor})

        return {
            "question": question,
            "competitors": competitors,
            "answers": answers,
            "rankings": rankings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
