import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from agents import Agent, Runner, trace, OpenAIChatCompletionsModel
from fastapi import APIRouter, HTTPException

router = APIRouter()

load_dotenv(override=True)


class FormattedEmailOutput(BaseModel):
    html_message: str
    pdf_message: str


@router.get("/api/fastapi/agents/tools")
async def openai_tool():
    try:
        instructions1 = (
            "You are a sales agent working for ComplAI, "
            "a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. "
            "You write professional, serious cold emails."
        )

        instructions2 = (
            "You are a humorous, engaging sales agent working for ComplAI, "
            "a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. "
            "You write witty, engaging cold emails that are likely to get a response."
        )

        openai_api_key = os.getenv("OPENAI_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if not openai_api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")
        if not google_api_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")

        openai_client = AsyncOpenAI(api_key=openai_api_key, base_url="https://api.openai.com/v1")
        gemini_client = AsyncOpenAI(
            api_key=google_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
        openai_model = OpenAIChatCompletionsModel(model="gpt-4o-mini", openai_client=openai_client)

        sales_agent1 = Agent(name="Open AI Sales Agent", instructions=instructions1, model=openai_model)
        sales_agent2 = Agent(name="Gemini Sales Agent", instructions=instructions2, model=gemini_model)

        description = "Write a cold sales email"

        tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
        tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)

        html_instructions = (
            "You can convert a text email body to an HTML email body. "
            "You are given a text email body which might have some markdown "
            "and you need to convert it to an HTML email body with simple, clear, compelling layout and design. "
            "Return only the HTML, with no markdown fences or extra commentary."
        )

        pdf_instructions = (
            "You can convert a text email body to a PDF-ready email body. "
            "You are given a text email body which might have some markdown "
            "and you need to convert it to a clean, print-friendly layout suitable for PDF export. "
            "Return only the formatted content, with no markdown fences or extra commentary."
        )

        html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-4o-mini")
        pdf_converter = Agent(name="PDF email body converter", instructions=pdf_instructions, model="gpt-4o-mini")

        html_tool = html_converter.as_tool(
            tool_name="html_converter",
            tool_description="Convert a text email body to an HTML email body",
        )
        pdf_tool = pdf_converter.as_tool(
            tool_name="pdf_converter",
            tool_description="Convert a text email body to a PDF-ready email body",
        )

        email_manager_instructions = (
            "You are an email formatter. You receive the body of the winning cold sales email. "
            "First use the html_converter tool to convert the body to HTML. "
            "Then use the pdf_converter tool to convert the same original body to a PDF-ready format. "
            "Your final output must include both converted versions in html_message and pdf_message."
        )

        email_manager = Agent(
            name="Email Manager",
            instructions=email_manager_instructions,
            tools=[html_tool, pdf_tool],
            model="gpt-4o-mini",
            output_type=FormattedEmailOutput,
            handoff_description="Convert the selected email to HTML and PDF formats",
        )

        sales_manager_instructions = """
        You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.

        Follow these steps carefully:
        1. Generate Drafts: Use both sales_agent tools to generate two different message drafts. Do not proceed until both drafts are ready.

        2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
        You can use the tools multiple times if you're not satisfied with the results from the first try.

        3. Handoff for Formatting: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will convert it to HTML and PDF.

        Crucial Rules:
        - You must use the sales agent tools to generate the drafts — do not write them yourself.
        - You must hand off exactly ONE email to the Email Manager — never more than one.
        """

        tools = [tool1, tool2]
        handoffs = [email_manager]

        sales_manager = Agent(
            name="Sales Manager",
            instructions=sales_manager_instructions,
            tools=tools,
            handoffs=handoffs,
            model="gpt-4o-mini",
        )

        message = "Send out a cold sales email addressed to Dear CEO from Alice"

        with trace("Automated SDR"):
            result = await Runner.run(sales_manager, message)

        formatted = result.final_output
        if not isinstance(formatted, FormattedEmailOutput):
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected agent output type: {type(formatted).__name__}",
            )

        return {
            "html_message": formatted.html_message,
            "pdf_message": formatted.pdf_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
