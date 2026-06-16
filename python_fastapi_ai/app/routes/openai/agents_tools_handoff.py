import os
from typing import Any

from agents import Agent, Runner, trace
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

load_dotenv(override=True)


class FormattedEmailOutput(BaseModel):
    subject: str
    html_message: str


def _serialize_output(output: Any) -> Any:
    if isinstance(output, BaseModel):
        return output.model_dump()
    if isinstance(output, dict):
        return output
    return str(output)


@router.get("/api/fastapi/openai/agents/tools_handoff")
async def openai_agents_tools_handoff():
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    try:
        # --- Step 1: Two sales agents exposed as tools ---
        sales_agent1 = Agent(
            name="Professional Sales Agent",
            instructions=(
                "You are a sales agent for ComplAI (SOC2 compliance SaaS). "
                "Write professional, serious cold emails."
            ),
            model="gpt-4o-mini",
        )
        sales_agent2 = Agent(
            name="Engaging Sales Agent",
            instructions=(
                "You are a sales agent for ComplAI (SOC2 compliance SaaS). "
                "Write witty, engaging cold emails likely to get a response."
            ),
            model="gpt-4o-mini",
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
            model="gpt-4o-mini",
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
            model="gpt-4o-mini",
        ).as_tool(
            tool_name="html_converter",
            tool_description="Convert a text email body to HTML",
        )

        formatter_agent = Agent(
            name="Email Formatter",
            instructions=(
                "You receive a winning cold email draft. "
                "Use subject_writer to create a subject, then html_converter to convert the body to HTML. "
                "Return subject and html_message as your final output."
            ),
            tools=[subject_tool, html_tool],
            model="gpt-4o-mini",
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
                3. Hand off ONLY the winning draft to the Email Formatter.

                Rules:
                - Use the sales agent tools to generate drafts — do not write them yourself.
                - Hand off exactly one email to the Email Formatter.
                """,
            tools=[tool1, tool2],
            handoffs=[formatter_agent],
            model="gpt-4o-mini",
        )

        message = "Write a cold sales email addressed to Dear Customer from Sarat"

        with trace("OpenAI Agents Tools Handoff Demo"):
            result = await Runner.run(sales_manager, message)

        return {"result": _serialize_output(result.final_output)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
