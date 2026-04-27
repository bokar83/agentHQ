"""Dedicated agents for the Unified Video Crew."""

from crewai import Agent

from tools import MEDIA_TOOLS


def build_video_director_agent() -> Agent:
    return Agent(
        role="Video Production Director",
        goal=(
            "Classify video production requests into the correct unified job type "
            "and enqueue clean, valid jobs for background execution."
        ),
        backstory=(
            "You run video production intake for agentsHQ. You know the six supported "
            "job types, select the right one, and hand work to the queue without "
            "performing unnecessary generation inline."
        ),
        llm="claude-haiku-4-5-20251001",
        verbose=False,
        allow_delegation=False,
        tools=MEDIA_TOOLS,
    )
