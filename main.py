from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from tavily import TavilyClient
from dotenv import load_dotenv
from pydantic import BaseModel
from prompts import RESEARCHER_PROMPT, CODE_WRITER_PROMPT, CODE_REVIEWER_PROMPT, CODE_FIXER_PROMPT

_ = load_dotenv()
search = TavilyClient()
model = ChatOpenAI(temperature=0.0)

class AgentState(TypedDict):
    problem: str 
    language: str
    content: str
    script: str 
    explanation: str
    critique: str
class ResearchOutput(BaseModel):
    language: str
    search_keywords: list[str]
class CodeWriterOutput(BaseModel):
    chain_of_thought: str
    explanation: str
    code: str
class CodeReviewerOutput(BaseModel):
    chain_of_thought: str
    critique: str
    
def researcher_agent(state: AgentState):
    problem = state['problem']
    if not problem:
        raise KeyError('The problem is not specified.')
    result = model.with_structured_output(ResearchOutput).invoke([SystemMessage(content=RESEARCHER_PROMPT), HumanMessage(content=problem)])
    
    content = []
    for q in result['search_keywords']:
        res = search.search(query=q, max_results=1)
        content.append(res['results'][0]['content'])
    
    return {'language': result.language, 'content': state.get('content', '') + '\n\n' + '\n\n'.join(content)}

def code_writer_agent(state: AgentState):
    problem = state['problem']
    lang = state['language']
    content = state['content']
    
    result = model.with_structured_output(CodeWriterOutput).invoke(CODE_WRITER_PROMPT.format(problem=problem, content=content, language=lang))
    
    return {'script': result.code, 'explanation': result.explanation}

def critique_agent(state: AgentState):
    script = state['script']
    problem = state['problem']
    
    result = model.with_structured_output(CodeReviewerOutput).invoke(CODE_REVIEWER_PROMPT.format(problem=problem, code=script))
    
    return {'critique': result.critique}

def code_fixer_agent(state: AgentState):
    critique = state['critique']
    code = state['script']
    problem = state['problem']
    content = state['content']
    language = state['language']
    
    
    result = model.with_structured_output(CodeWriterOutput).invoke(CODE_FIXER_PROMPT.format(problem=problem, language=language, research=content, critique=critique, code=code))
    
    return {'script': result.code, 'explanation': result.explanation}

graph = StateGraph(AgentState)

graph.add_node('researcher', researcher_agent)
graph.add_node('code_writer', code_writer_agent)
graph.add_node('critique', critique_agent)
graph.add_node('code_fixer', code_fixer_agent)

graph.set_entry_point('researcher')

graph.add_edge('researcher', 'code_writer')
graph.add_edge('code_writer', 'critique')
graph.add_edge('critique', 'code_fixer')
graph = graph.compile()
if __name__ == '__main__':
    prompt = input('Problem description: ')
    while not prompt.strip():
        print('Provide valid prompt.')
        prompt = input('Problem description: ')
    result = graph.invoke({
        'problem': prompt
    })
    print(result['explanation'])
    print('=================')
    print(result['script'])