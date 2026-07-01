import asyncio

from agents import Runner, trace, gen_trace_id
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import APIConnectionError
from pydantic import BaseModel, Field

from .search_agent import search_agent
from .planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from .writer_agent import writer_agent, ReportData

router = APIRouter()

load_dotenv(override=True)


class DeepResearchRequest(BaseModel):
    """Client-provided payload for the deep research endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        description="The research question to investigate.",
        examples=["What are the latest advances in solid-state batteries?"],
    )


class DeepResearchResponse(BaseModel):
    """Formatted deep research result returned to the client."""

    query: str = Field(description="The original query that was researched.")
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The full report in markdown format.")
    follow_up_questions: list[str] = Field(
        default_factory=list, description="Suggested topics to research further."
    )
    trace_id: str = Field(description="OpenAI trace id for this research run.")
    trace_url: str = Field(description="Link to view the trace on the OpenAI platform.")
    status_updates: list[str] = Field(
        default_factory=list, description="Step-by-step progress of the research run."
    )


class DeepResearchEnvelope(BaseModel):
    """Top-level response envelope that nests the deep research report."""

    deep_research_report: DeepResearchResponse = Field(
        description="The formatted deep research report for the client query."
    )


@router.post(
    "/api/fastapi/openai/agents/deepsearch/research_manager",
    response_model=DeepResearchEnvelope,
)
async def openai_agents_deepsearch_manager(request: DeepResearchRequest) -> DeepResearchEnvelope:
    """Run the deep research process for the client query and return the formatted report."""
    try:
        manager = ResearchManager()
        result = await manager.run(request.query)
        return DeepResearchEnvelope(deep_research_report=result)
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach the LLM API. Check network, proxy, VPN, or API key settings.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ResearchManager:

    async def run(self, query: str) -> DeepResearchResponse:
        """Run the deep research process and return the final formatted report."""
        status_updates: list[str] = []

        trace_id = gen_trace_id()
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"

        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: {trace_url}")
            status_updates.append(f"View trace: {trace_url}")

            print("Starting research...")
            search_plan = await self.plan_searches(query)
            status_updates.append("Searches planned, starting to search...")

            search_results = await self.perform_searches(search_plan)
            status_updates.append("Searches complete, writing report...")

            report = await self.write_report(query, search_results)
            status_updates.append("Report complete.")

        return DeepResearchResponse(
            query=query,
            short_summary=report.short_summary,
            markdown_report=report.markdown_report,
            follow_up_questions=report.follow_up_questions,
            trace_id=trace_id,
            trace_url=trace_url,
            status_updates=status_updates,
        )

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
