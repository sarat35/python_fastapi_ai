import os
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OpenAIChatCompletionsModel,
    Runner,
    input_guardrail,
    trace,
)
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, AsyncOpenAI
from pydantic import BaseModel

router = APIRouter()

load_dotenv(override=True)


class FormattedEmailOutput(BaseModel):
    subject: str
    html_message: str

class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str


def _serialize_output(output: Any) -> Any:
    if isinstance(output, BaseModel):
        return output.model_dump()
    if isinstance(output, dict):
        return output
    return str(output)


def _get_model() -> OpenAIChatCompletionsModel:
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if openai_api_key:
        client = AsyncOpenAI(api_key=openai_api_key, base_url="https://api.openai.com/v1")
        return OpenAIChatCompletionsModel(model="gpt-4o-mini", openai_client=client)

    if google_api_key:
        client = AsyncOpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        return OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)

    
    raise HTTPException(
        status_code=500,
        detail="GOOGLE_API_KEY or OPENAI_API_KEY must be set",
    )


@router.get("/api/fastapi/openai/agents/tools_handoff_guardrails")
async def openai_agents_tools_handoff_guardrails():
    model = _get_model()

    try:
        guardrail_agent = Agent(
            name="Name check",
            instructions="Check if the user is including someone's personal name in what they want you to do.",
            output_type=NameCheckOutput,
            model=model,
        )

        @input_guardrail
        async def guardrail_against_name(ctx, agent, message):
            result = await Runner.run(guardrail_agent, message, context=ctx.context)
            is_name_in_message = result.final_output.is_name_in_message
            return GuardrailFunctionOutput(
                output_info={"found_name": result.final_output},
                tripwire_triggered=is_name_in_message,
            )

        # --- Step 1: Two sales agents exposed as tools ---
        sales_agent1 = Agent(
            name="Professional Sales Agent",
            instructions=(
                "You are a sales agent for ComplAI (SOC2 compliance SaaS). "
                "Write professional, serious cold emails."
            ),
            model=model,
        )
        sales_agent2 = Agent(
            name="Engaging Sales Agent",
            instructions=(
                "You are a sales agent for ComplAI (SOC2 compliance SaaS). "
                "Write witty, engaging cold emails likely to get a response."
            ),
            model=model,
        )

        tool1 = sales_agent1.as_tool(
            tool_name="sales_agent1",
            tool_description="Write a professional cold sales email",
        )
        tool2 = sales_agent2.as_tool(
            tool_name="sales_agent2",
            tool_description="Write an engaging cold sales email",
        )

        # --- Step 2: Formatter agent (handoff target) with its own tools ---
        subject_tool = Agent(
            name="Subject Writer",
            instructions="Write a compelling subject line for a cold sales email.",
            model=model,
        ).as_tool(
            tool_name="subject_writer",
            tool_description="Write a subject for a cold sales email",
        )

        html_tool = Agent(
            name="HTML Converter",
            instructions=(
                "Convert a text email body to clean HTML. "
                "Return only the HTML, no markdown fences."
            ),
            model=model,
        ).as_tool(
            tool_name="html_converter",
            tool_description="Convert a text email body to HTML",
        )

        formatter_agent = Agent(
            name="Email_Formatter",
            instructions=(
                "You receive a winning cold email draft. "
                "Use subject_writer to create a subject, then html_converter to convert the body to HTML. "
                "Return subject and html_message as your final output."
            ),
            tools=[subject_tool, html_tool],
            model=model,
            output_type=FormattedEmailOutput,
            handoff_description="Format the selected email with a subject and HTML body",
        )

        # --- Step 3: Sales Manager uses tools, then hands off to formatter ---
        sales_manager = Agent(
            name="Sales Manager",
            instructions="""
You are a Sales Manager at ComplAI.

1. Use both sales_agent tools to generate two email drafts.
2. Pick the single best draft.
3. Hand off ONLY the winning draft to the Email_Formatter.

Rules:
- Use the sales agent tools to generate drafts — do not write them yourself.
- Hand off exactly one email to the Email_Formatter.
""",
            tools=[tool1, tool2],
            handoffs=[formatter_agent],
            input_guardrails=[guardrail_against_name],
            model=model,
        )

        message1 = "Write a cold sales email addressed to Dear Customer from Sarat Thokala"
        #message2 = "Send out a cold sales email addressed to Dear CEO from Head of Business Development"

        print(f"Testing with message: {message1}")

        with trace("OpenAI Agents Tools Handoff Demo"):
            result = await Runner.run(sales_manager, message1)

        return {"result": _serialize_output(result.final_output)}
    except InputGuardrailTripwireTriggered as e:
        found_name = e.guardrail_result.output.output_info.get("found_name")
        return {
            "guardrail_triggered": True,
            "found_name": _serialize_output(found_name),
        }
    except HTTPException:
        raise
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach the LLM API. Check network, proxy, VPN, or API key settings.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
