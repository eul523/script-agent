from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from tavily import TavilyClient
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

_ = load_dotenv()
search = TavilyClient()

class AgentState(TypedDict):
    problem: str 
    content: str
    script: str 
    critique: str
    tests: list[dict[str, str]]
    
def research_agent(state: AgentState):
    