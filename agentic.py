from typing import TypedDict, Literal
import json
import random
from langgraph.graph import END, StateGraph
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod
from langchain_core.messages import HumanMessage
import os
from typing import Annotated, Literal, TypedDict
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import functools
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import codecs
from question_utilities import QuestionUtilities
import ui_utilities
import templateprompts
from dotenv import load_dotenv
from langgraph.types import interrupt, Command
from langchain.tools.retriever import create_retriever_tool
import re
from processors.vectordb_processor import VectorDbProcessor
import traceback
import uuid

load_dotenv()

util = QuestionUtilities()


class NMAgentState(TypedDict):
    """
    Encapsulates state in our agentic workflow
    """
    messages: Annotated[list, add_messages]

class AgenticWorkflow():
    def __init__(self, llm, embed_llm):
        self.llm = llm
        self.embed_model = embed_llm
        self.workflow = StateGraph(NMAgentState)
        
        # tools
        processor = VectorDbProcessor(llm=self.llm, embed_model=self.embed_model, collection_name='scholarships',)
        reporter_tool = create_retriever_tool(processor.vector_store.as_retriever(),"retrieve_document_links", templateprompts.reporter_tool_prompt_template,) 
        
        # agents
        screener_agent = self.create_agent(self.llm, [], templateprompts.screener_template)
        interviewer_agent = self.create_agent(self.llm, [], templateprompts.interviewer_template)
        reporter_agent = self.create_agent(self.llm, [], templateprompts.reporter_template)
        
        # nodes
        screener_node = functools.partial(self.agent_node, agent=screener_agent, name="Screener Agent")
        interviewer_node = functools.partial(self.agent_node, agent=interviewer_agent, name="Interviewer Agent")
        reporter_node = functools.partial(self.agent_node, agent=reporter_agent, name="Reporter Agent")
        reporter_tool_node = ToolNode([reporter_tool])
    
        # add nodes
        self.workflow.add_node("screener", screener_node)
        self.workflow.add_node("interviewer", interviewer_node)
        self.workflow.add_node("reporter", reporter_node)
        self.workflow.add_node("reporter-tools", reporter_tool_node)
        
        # add entrypoint
        self.workflow.set_entry_point("screener")
        
        # add edges
        self.workflow.add_edge("screener", "interviewer")
        self.workflow.add_conditional_edges("interviewer", self.should_continue_interview)
        self.workflow.add_conditional_edges("reporter", self.should_generate_report)
        self.workflow.add_edge("reporter", END)
        self.workflow.add_edge("reporter-tools", "reporter")
        
        # compile the self.workflow into a graph
        checkpointer = MemorySaver()
        self.graph = self.workflow.compile(checkpointer=checkpointer)

        
    def create_agent(self, llm, tools, system_message: str):
        """
        Creates an agent with the given LLM, tools, and system message
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        prompt = prompt.partial(system_message=system_message)
        if tools:
          return prompt | llm.bind_tools(tools)
        else:
          return prompt | llm
    
    #####################################
    ## NODES ##
    #####################################
    def agent_node(self, state, agent, name):
        """
        Creates an agent node
        """
        output = agent.invoke(state)
        results = [output]
        
        # Append new, not-yet-complete interview questions if there are any that should be answered
        if next_questions := util.next_questions(output.content):
            results += [HumanMessage(content=interrupt(next_questions))]
            
        return { "messages": results }
    
    #####################################
    ## CONDITIONAL EDGES ##
    #####################################
    def should_continue_interview(self, state) -> Literal['interviewer','reporter']:
        if util.is_in_interview_mode():
            return "interviewer"
        else:
            return "reporter"
        
    def should_generate_report(self, state) -> Literal['reporter-tools', END]:
      if len(state['messages']) and 'tool_calls' in state['messages'][-1] and state['messages'][-1].tool_calls:
          return "reporter-tools"
      else:
          return END
     
    #####################################
    ## DRIVER METHOD ##
    ##################################### 
    def run(self, prompt, st, stream=None):
        """
        Executes the workflow.
        """
                
        config = {"configurable": {"thread_id": uuid.uuid4(), "recursion_limit": 5}}
        
        try:
            with st.container(height=500):
                for event in (stream or self.graph.stream({"messages": [HumanMessage(content=prompt)]}, config, stream_mode="values")):
                    if '__interrupt__' in event:
                        if input_text := ui_utilities.handle_interrupt(event['__interrupt__'], config, st) :
                            stream = self.graph.stream(Command(resume=input_text), config=self.graph.get_state(config).config, stream_mode="values")
                            self.run(input_text, st, stream)
                         
                    else:
                        response_content = event['messages'][-1].content
                        ui_utilities.render_question_chat(response_content, config, st)
                        st.session_state.messages2.append({"role": "assistant", "content": response_content})
                        
        except Exception as e:
            print(f"\n\nErrors generating response:\n===============\n {str(e)}")
            traceback.print_exc()

