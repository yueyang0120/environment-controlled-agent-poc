"""
Environment-Controlled Agent with Perception-Reasoning-Action-Feedback Loop.
"""

from typing import TypedDict, Dict, Any, List, Callable, Optional, Annotated, Literal
import os
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Import Tavily for web search
try:
    from langchain_tavily import TavilySearch
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️ Tavily not available. Web search will use fallback mode.")

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Load environment variables
load_dotenv()

# Gmail configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "your_email@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your_app_password_here")

# Human-in-the-loop configuration
HUMAN_CONFIRMATION_TOOLS = {
    "send_email": {
        "description": "Send email via Gmail",
        "confirmation_message": "📧 Email Draft Ready for Review",
        "requires_confirmation": True
    }
}

# Tool descriptions for LLM reasoning
TOOL_DESCRIPTIONS = """
Available Tools:
1. run_python - Execute Python code for calculations and data processing
   Input: Python code as string
   Example: "25 * 8 + 15" or "import math; math.sqrt(144)"

2. send_email - Send email via Gmail (requires human confirmation)
   Input: "to:email@domain.com|subject:Subject Text|body:Message content"
   Example: "to:john@example.com|subject:Hello|body:How are you?"

3. draft_email - Create email draft without sending
   Input: Same format as send_email
   
4. search_web - Search the web for real-time information with full content extraction
   Input: Search query as string
   Example: "latest news about AI" or "weather in New York" or "what is quantum computing"
   Note: Provides comprehensive information including full article content, not just snippets
   Returns: Query-matched excerpts + complete article content from multiple sources
"""

# ============================================================================
# STATE DEFINITION
# ============================================================================


class AgentState(TypedDict, total=False):
    """
    Comprehensive state definition for the agent workflow.

    This TypedDict defines all possible state variables that can be passed
    between nodes in the agent graph.
    """
    # Core workflow fields
    query: str                 # User input query
    perception: str            # Parsed task/context understanding
    plan: str                  # LLM's next action description
    action_input: str          # Parameters for the selected action
    action_name: str           # Name of the tool to use
    action_result: str         # Tool execution output
    feedback: str              # Evaluation of the result
    goal_met: bool             # Whether the task is completed
    iterations: int            # Current iteration count
    final_answer: str          # Final response to user
    max_iterations: int        # Maximum allowed iterations
    next_step_needed: str      # What should happen next if goal not met
    action_history: List[str]  # History of actions taken to prevent loops

    # Human-in-the-loop fields
    needs_confirmation: bool   # Whether current action needs approval
    user_confirmation: str     # User's confirmation response
    confirmation_pending: bool  # Whether waiting for user input
    draft_content: str         # Content to show user for confirmation


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class LLMManager:
    """Manages LLM instances and configurations."""

    @staticmethod
    def get_llm(temperature: float = 0) -> ChatOpenAI:
        """
        Initialize the LLM with specified temperature.

        Args:
            temperature: Controls randomness in responses (0.0 = deterministic)

        Returns:
            Configured ChatOpenAI instance
        """
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=temperature,
        )


class EmailManager:
    """Handles all email-related operations."""

    @staticmethod
    def parse_email_data(email_data: str) -> Dict[str, str]:
        """
        Parse email data from various formats.

        Args:
            email_data: Email data in JSON or pipe-separated format

        Returns:
            Dictionary with 'to', 'subject', and 'body' keys
        """
        if email_data.startswith("{"):
            # JSON format
            data = json.loads(email_data)
            return {
                "to": data.get("to", ""),
                "subject": data.get("subject", ""),
                "body": data.get("body", "")
            }
        else:
            # Pipe-separated format: "to:email|subject:text|body:text"
            parts = email_data.split("|")
            result = {"to": "", "subject": "", "body": ""}

            for part in parts:
                if part.startswith("to:"):
                    result["to"] = part[3:].strip()
                elif part.startswith("subject:"):
                    result["subject"] = part[8:].strip()
                elif part.startswith("body:"):
                    result["body"] = part[5:].strip()

            return result

    @staticmethod
    def send_gmail(email_data: str) -> str:
        """
        Send an email using Gmail SMTP.

        Args:
            email_data: Email data in supported format

        Returns:
            Success or error message
        """
        try:
            # Validate Gmail configuration
            if GMAIL_EMAIL == "your_email@gmail.com" or not GMAIL_EMAIL:
                return "Error: Gmail email not configured. Please set GMAIL_EMAIL in your .env file."
            
            if GMAIL_APP_PASSWORD == "your_app_password_here" or not GMAIL_APP_PASSWORD:
                return "Error: Gmail app password not configured. Please set GMAIL_APP_PASSWORD in your .env file."
            
            parsed = EmailManager.parse_email_data(email_data)

            # Validate required fields
            if not parsed["to"]:
                return "Error: No recipient email address provided"

            # Set defaults for optional fields
            subject = parsed["subject"] or "Message from AI Agent"
            body = parsed["body"] or "This is an automated message from your AI agent."

            # Create and configure message
            msg = MIMEMultipart()
            msg['From'] = GMAIL_EMAIL
            msg['To'] = parsed["to"]
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send via Gmail SMTP
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

            clean_password = GMAIL_APP_PASSWORD.replace(" ", "")
            server.login(GMAIL_EMAIL, clean_password)

            server.sendmail(GMAIL_EMAIL, parsed["to"], msg.as_string())
            server.quit()

            return f"Email successfully sent to {parsed['to']} with subject '{subject}'"

        except json.JSONDecodeError as e:
            return f"Error parsing email data: {str(e)}. Use format: to:email@domain.com|subject:Your Subject|body:Your message"
        except smtplib.SMTPAuthenticationError:
            return "Error: Gmail authentication failed. Please check your GMAIL_EMAIL and GMAIL_APP_PASSWORD in the .env file."
        except smtplib.SMTPRecipientsRefused:
            return f"Error: Recipient email address '{parsed['to']}' was refused by the server."
        except Exception as e:
            return f"Error sending email: {str(e)}"

    @staticmethod
    def draft_email(email_data: str) -> str:
        """
        Create an email draft without sending it.

        Args:
            email_data: Email data in supported format

        Returns:
            Formatted email draft for user review
        """
        try:
            parsed = EmailManager.parse_email_data(email_data)

            if not parsed["to"]:
                return "Error: No recipient email address provided"

            subject = parsed["subject"] or "Please provide the subject"
            body = parsed["body"] or "Please provide the message content"

            return f"""
📧 EMAIL DRAFT
==============
To: {parsed["to"]}
Subject: {subject}

Message:
{body}
==============
"""
        except Exception as e:
            return f"Error creating email draft: {str(e)}"


class PythonExecutor:
    """Handles Python code execution with safety measures."""

    @staticmethod
    def run_python(code: str) -> str:
        """
        Execute Python code safely.

        Args:
            code: Python code to execute

        Returns:
            Execution result or error message
        """
        try:
            # Create a restricted environment
            allowed_modules = {
                'math': __import__('math'),
                'random': __import__('random'),
                'datetime': __import__('datetime'),
                'json': __import__('json'),
                're': __import__('re'),
            }

            # Prepare execution environment
            exec_globals = {
                '__builtins__': {
                    'abs': abs, 'round': round, 'min': min, 'max': max,
                    'sum': sum, 'len': len, 'range': range, 'enumerate': enumerate,
                    'zip': zip, 'map': map, 'filter': filter, 'sorted': sorted,
                    'str': str, 'int': int, 'float': float, 'bool': bool,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'print': print,
                },
                **allowed_modules
            }
            exec_locals = {}

            # Try to evaluate as expression first (for simple calculations)
            try:
                result = eval(code, exec_globals, exec_locals)
                return str(result)
            except:
                # If eval fails, try exec (for statements)
                exec(code, exec_globals, exec_locals)

                # Return the result of the last expression if available
                if exec_locals:
                    last_value = list(exec_locals.values())[-1]
                    return str(last_value)
                else:
                    return "Code executed successfully (no return value)"

        except Exception as e:
            return f"Error in calculation '{code}': {str(e)}"


class SearchManager:
    """Handles search operations using Tavily web search."""

    @staticmethod
    def intelligent_format_data(content: str, query: str) -> str:
        """
        Use AI to intelligently format raw data into user-friendly content.
        
        Args:
            content: Raw content that might contain structured data
            query: Original user query for context
            
        Returns:
            AI-formatted, user-friendly content
        """
        # If content looks like it might benefit from formatting
        if any(indicator in content for indicator in ['{', ':', '_', 'temp_c', 'price', 'USD', 'api']):
            try:
                llm = LLMManager.get_llm(temperature=0)
                
                format_prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content="""You are an expert at making data user-friendly and readable.

Your task is to take raw search results or structured data and format it beautifully for humans.

GUIDELINES:
- If you see raw JSON or API data, convert it to natural, readable text
- Use emojis and formatting to make information clear and engaging
- For weather data: show temperature, conditions, location clearly
- For financial data: highlight prices, changes, market info
- For dates/times: make them human-readable
- For technical data: explain in simple terms
- Keep all important information but make it digestible
- Use bullet points, headers, and structure for clarity

The goal is to make the information immediately useful and easy to understand for any user."""),
                    HumanMessage(content=f"""Please format this search result data to be user-friendly and readable.

Original Query: {query}

Raw Data:
{content}

Please reformat this into clear, engaging, human-readable content that directly answers the user's query:""")
                ])
                
                chain = format_prompt | llm
                formatted_result = chain.invoke({})
                return formatted_result.content
                
            except Exception as e:
                # If AI formatting fails, return original content
                return content
        
        return content

    @staticmethod
    def search_web(query: str) -> str:
        """
        Search the web using Tavily search engine with intelligent formatting.

        Args:
            query: Search query string

        Returns:
            Search results with AI-formatted content
        """
        if not TAVILY_AVAILABLE:
            return (
                f"Web search is not available (Tavily not installed). "
                f"However, I can help you with calculations and email tasks. "
                f"Please try asking for a calculation or email instead."
            )
        
        # Check if TAVILY_API_KEY is set
        if not os.getenv("TAVILY_API_KEY"):
            return (
                f"Web search requires TAVILY_API_KEY to be set in environment variables. "
                f"Please get an API key from https://tavily.com and set it in your .env file. "
                f"For now, I can help you with calculations and email tasks."
            )
        
        try:
            # Initialize Tavily search with enhanced settings for full content
            search_tool = TavilySearch(
                max_results=10,
                include_raw_content=True  # Enable full content extraction
            )
            
            # Perform the search
            search_results = search_tool.invoke(query)
            
            # Format the results with intelligent formatting
            if isinstance(search_results, dict) and 'results' in search_results:
                formatted_results = f"🔍 Web Search Results for: '{query}'\n\n"
                
                # Add the main answer if available
                if search_results.get('answer'):
                    formatted_results += f"📝 **Quick Summary:** {search_results['answer']}\n\n"
                
                # Add individual results with intelligent formatting
                for i, result in enumerate(search_results['results'], 1):
                    title = result.get('title', 'No title')
                    url = result.get('url', 'No URL')
                    snippet = result.get('content', 'No snippet')
                    raw_content = result.get('rawContent', '')
                    
                    formatted_results += f"**{i}. {title}**\n"
                    formatted_results += f"🔗 Source: {url}\n\n"
                    
                    # Intelligently format snippet
                    if snippet:
                        formatted_snippet = SearchManager.intelligent_format_data(snippet, query)
                        formatted_results += f"📝 **Key Information:**\n{formatted_snippet}\n\n"
                    
                    # Intelligently format full content if available
                    if raw_content:
                        # Clean raw content
                        cleaned_content = raw_content.strip()
                        
                        # Use AI to format the content intelligently
                        formatted_content = SearchManager.intelligent_format_data(cleaned_content, query)
                        
                        # Limit content length but keep it substantial
                        max_content_length = 3000
                        if len(formatted_content) > max_content_length:
                            formatted_content = formatted_content[:max_content_length] + "\n\n[Content truncated - full information available in source...]"
                        
                        formatted_results += f"📄 **Detailed Information:**\n{formatted_content}\n\n"
                    else:
                        formatted_results += "📄 **Detailed Information:** Not available\n\n"
                    
                    formatted_results += "---\n\n"  # Separator between results
                
                # Add follow-up questions if available
                if search_results.get('follow_up_questions'):
                    formatted_results += "🤔 **Related Questions:**\n"
                    for question in search_results['follow_up_questions']:
                        formatted_results += f"   • {question}\n"
                
                return formatted_results
            else:
                return f"Search completed for '{query}' but no results were found in the expected format."
                
        except Exception as e:
            return f"Error performing web search for '{query}': {str(e)}. Please check your TAVILY_API_KEY and internet connection."


# ============================================================================
# WORKFLOW NODES
# ============================================================================

class WorkflowNodes:
    """Contains all workflow node implementations."""

    @staticmethod
    def perception_node(state: AgentState) -> AgentState:
        """
        Parse user query into task description and sub-goals.

        This node analyzes the user's input and creates a clear understanding
        of what needs to be accomplished.
        """
        print("\n🔍 PERCEPTION PHASE")

        # Initialize iterations counter
        if "iterations" not in state or state["iterations"] is None:
            state["iterations"] = 0
        else:
            state["iterations"] += 1

        llm = LLMManager.get_llm()

        # Always analyze the original query for meaningful breakdown
        query_text = state.get("query", "")
        if not query_text:
            print("ERROR: No query found in state!")
            state["perception"] = "No query provided"
            return state

        # Check if we have meaningful previous context for refinement
        has_meaningful_context = (
            state["iterations"] > 0 and 
            state.get('action_name') and 
            state.get('action_result') and 
            state.get('feedback') and
            not state.get('goal_met', False)
        )

        if has_meaningful_context:
            # Check if we're in a loop (same action repeated)
            if state.get('action_name') == 'search_web' and 'Web Search Results' in state.get('action_result', ''):
                # We already have search results, task should be complete
                state["perception"] = f"Task completed: Successfully found information about '{query_text}' through web search. The search results provide comprehensive information that answers the user's query."
                print(f"Perception: {state['perception']}")
                return state
            
            # Subsequent iterations: refine based on feedback only if we have meaningful context
            perception_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content="You are an expert at understanding tasks and determining if they are complete based on previous actions."),
                HumanMessage(
                    content=f"""Original query: {query_text}

Previous action taken: {state.get('action_name', '')}
Result obtained: {state.get('action_result', '')[:300]}...
Feedback: {state.get('feedback', '')}
Iteration: {state.get('iterations', 0)}

IMPORTANT: If the previous action was 'search_web' and it returned web search results, the task is likely COMPLETE.
If the previous action was 'draft_email' and it created a draft, the next step should be to send the email.
If the previous action was 'run_python' and it calculated something, the task is likely COMPLETE.

Analyze if the task is complete or what specific next step is needed (avoid repeating the same action).""")
            ])
        else:
            # First iteration or no meaningful context: analyze original query
            perception_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content="You are an expert at understanding user queries and breaking them down into clear, actionable tasks."),
                HumanMessage(
                    content=f"Analyze this query and provide:\n1. A clear task description\n2. What specific action needs to be taken\n3. What the expected outcome should be\n\nQuery: {query_text}")
            ])

        chain = perception_prompt | llm
        perception_result = chain.invoke({})
        state["perception"] = perception_result.content

        print(f"Perception: {state['perception']}")
        return state

    @staticmethod
    def reasoning_node(state: AgentState) -> AgentState:
        """
        Select appropriate tools and plan actions based on perception.

        This node uses intelligent reasoning to choose the best tool
        for the current task.
        """
        print("\n🧠 REASONING PHASE")

        llm = LLMManager.get_llm()

        query = state.get("query", "")
        perception = state.get("perception", "")
        previous_action = state.get("action_name", "")
        previous_result = state.get("action_result", "")
        feedback = state.get("feedback", "")
        iterations = state.get("iterations", 0)
        
        # Initialize action history if not exists
        if "action_history" not in state:
            state["action_history"] = []
        
        # Check for potential loops
        action_history = state.get("action_history", [])
        recent_actions = action_history[-3:] if len(action_history) >= 3 else action_history

        reasoning_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are an intelligent agent that selects the best tool for a given task.

{TOOL_DESCRIPTIONS}

Guidelines:
1. For mathematical calculations, use 'run_python'
2. For email tasks:
   - PREFER 'draft_email' first to let user review content before sending
   - Only use 'send_email' if user explicitly wants to send immediately OR if you already drafted and user confirmed
3. For web searches and real-time information:
   - Use 'search_web' for current events, news, weather, recent information
   - Use 'search_web' for factual questions you're unsure about
   - Use 'search_web' for topics that change frequently (prices, stocks, weather, etc.)
4. Extract parameters intelligently from the user's query
5. Consider the workflow: draft → review → send (not direct send)

IMPORTANT LOOP PREVENTION:
- If the same action was recently performed and got results, DO NOT repeat it
- If 'search_web' already returned results, the task is likely COMPLETE
- If 'run_python' already calculated something, the task is likely COMPLETE
- Only repeat an action if the previous attempt failed or was incomplete

Respond with a JSON object:
```json
{{
    "intent_analysis": "brief analysis of what the user wants",
    "tool_reasoning": "why you chose this specific tool and workflow step",
    "action_name": "tool_name",
    "action_input": "input for the tool"
}}
```"""),
            HumanMessage(content=f"""
Query: {query}
Task understanding: {perception}
Previous action: {previous_action}
Previous result: {previous_result}
Feedback: {feedback}
Iteration: {iterations}
Recent action history: {recent_actions}

IMPORTANT: Check if the task is already complete based on previous results. If 'search_web' already returned good results, or if 'run_python' already calculated the answer, you may not need to take any action.

Select the best tool and provide the input:""")
        ])

        chain = reasoning_prompt | llm
        reasoning_result = chain.invoke({})

        try:
            # Parse JSON response
            response_content = reasoning_result.content
            print(f"Raw reasoning response: {response_content[:200]}...")

            if "```json" in response_content:
                response_content = response_content.split(
                    "```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split(
                    "```")[1].split("```")[0].strip()

            reasoning_data = json.loads(response_content)

            state["plan"] = f"Intent: {reasoning_data.get('intent_analysis', '')}\nReasoning: {reasoning_data.get('tool_reasoning', '')}"
            state["action_name"] = reasoning_data.get("action_name", "")
            state["action_input"] = reasoning_data.get("action_input", "")
            
            # Add to action history if we have a valid action
            if state["action_name"]:
                action_history = state.get("action_history", [])
                action_history.append(state["action_name"])
                state["action_history"] = action_history

            print(
                f"🎯 Intent Analysis: {reasoning_data.get('intent_analysis', '')}")
            print(
                f"🤔 Tool Reasoning: {reasoning_data.get('tool_reasoning', '')}")
            print(f"✅ Selected Action: {state['action_name']}")
            print(f"📝 Action Input: {state['action_input'][:100]}...")

            # Check if action needs confirmation
            if state["action_name"] in HUMAN_CONFIRMATION_TOOLS:
                state["needs_confirmation"] = True
                state["confirmation_pending"] = True
                print(
                    f"⚠️ Action '{state['action_name']}' requires human confirmation")

                # Create draft for email actions
                if state["action_name"] == "send_email":
                    draft_result = EmailManager.draft_email(
                        state["action_input"])
                    state["draft_content"] = draft_result
            else:
                state["needs_confirmation"] = False
                state["confirmation_pending"] = False

        except Exception as e:
            print(f"Error parsing reasoning response: {e}")
            print(f"Full response: {reasoning_result.content}")

            # Check if the response indicates task completion
            response_lower = reasoning_result.content.lower()
            if any(phrase in response_lower for phrase in ["task is complete", "already complete", "no action needed", "goal is met"]):
                state["action_name"] = ""
                state["action_input"] = ""
                state["plan"] = "Task appears to be already complete based on previous results"
                state["needs_confirmation"] = False
                state["goal_met"] = True
                
                # Create final answer from previous results
                if state.get("action_result"):
                    state["final_answer"] = f"Based on the previous results: {state['action_result']}"
                else:
                    state["final_answer"] = "Task completed based on previous analysis"
                
                print("🎯 Task identified as complete - no further action needed")
                return state

            # Fallback logic for parsing errors
            if "calculate" in query.lower() or any(op in query for op in ['+', '-', '*', '/', '^']):
                state["action_name"] = "run_python"
                state["action_input"] = query
            elif "email" in query.lower():
                state["action_name"] = "draft_email"
                state["action_input"] = query
            else:
                state["action_name"] = "search_web"
                state["action_input"] = query

            state["plan"] = "Fallback reasoning due to parsing error"
            state["needs_confirmation"] = False

        return state

    @staticmethod
    def action_node(state: AgentState) -> AgentState:
        """
        Execute the selected action using the appropriate tool.

        This node runs the chosen tool with the provided input
        and captures the result.
        """
        print("\n🔧 ACTION PHASE")

        action_name = state.get("action_name", "")
        action_input = state.get("action_input", "")
        needs_confirmation = state.get("needs_confirmation", False)
        user_confirmation = state.get("user_confirmation", "")
        
        # If no action is specified, task is likely complete
        if not action_name:
            print("⏸️ No action specified - task appears to be complete")
            state["action_result"] = "Task completed - no action needed"
            return state

        # Skip execution if confirmation is needed but not provided
        if needs_confirmation and user_confirmation not in ['y', 'yes']:
            print(
                f"⏸️ Skipping action '{action_name}' - waiting for user confirmation")
            state["action_result"] = "Waiting for user confirmation"
            return state

        # Tool registry
        tools = {
            "run_python": PythonExecutor.run_python,
            "send_email": EmailManager.send_gmail,
            "draft_email": EmailManager.draft_email,
            "search_web": SearchManager.search_web,
        }

        if action_name in tools:
            try:
                start_time = time.time()
                result = tools[action_name](action_input)
                elapsed = time.time() - start_time

                state["action_result"] = str(result)
                print(f"Action completed in {elapsed:.2f}s: {action_name}")
                print(f"Result (truncated): {str(result)[:100]}...")
            except Exception as e:
                state["action_result"] = f"Error executing {action_name}: {str(e)}"
                print(f"Action error: {e}")
        else:
            state["action_result"] = f"Unknown action: {action_name}"
            print(f"Unknown action: {action_name}")

        return state

    @staticmethod
    def feedback_node(state: AgentState) -> AgentState:
        """
        Evaluate results and determine if the goal is met.

        This node assesses whether the action result satisfies
        the original user query.
        """
        print("\n📝 FEEDBACK PHASE")

        llm = LLMManager.get_llm()

        query = state.get("query", "")
        perception = state.get("perception", "")
        action_name = state.get("action_name", "")
        action_input = state.get("action_input", "")
        action_result = state.get("action_result", "")
        max_iterations = state.get("max_iterations", 5)

        feedback_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are evaluating whether an action result satisfies the user's query.

IMPORTANT EVALUATION CRITERIA:
- For email tasks: 'draft_email' creates a draft but does NOT complete the task - user still needs to send it
- For calculations: result must be correct and complete
- For web searches: if search results are returned with relevant information, the task IS COMPLETE
- For simple factual questions: if the information is provided, the task IS COMPLETE
- Only mark goal_met=true if the user's ORIGINAL intent is fully satisfied

SPECIAL CASES:
- If action was 'search_web' and results contain relevant information about the query, mark goal_met=true
- If user asked a simple question and got a comprehensive answer, mark goal_met=true
- Don't require additional actions unless specifically needed

IMPORTANT: When goal_met=true, provide the FULL detailed result as final_answer, do NOT summarize.
Preserve all the rich content, formatting, and details from the action result.

Review the action result and determine:
1. If the result fully satisfies the user's original intent
2. If not, what's the next logical step needed

Respond with a JSON object:
```json
{
    "feedback": "your detailed assessment of the result",
    "goal_met": boolean,
    "next_step_needed": "what should happen next (if goal not met)",
    "final_answer": "the COMPLETE and DETAILED result from action_result (do NOT summarize, preserve all formatting and content)"
}
```"""),
            HumanMessage(
                content=f"Original query: {query}\nTask understanding: {perception}\nAction performed: {action_name}\nAction input: {action_input}\nAction result: {action_result}\n\nEvaluate if this result FULLY satisfies the user's original intent:")
        ])

        chain = feedback_prompt | llm
        feedback_result = chain.invoke({})

        try:
            # Parse JSON response
            response_content = feedback_result.content
            if "```json" in response_content:
                response_content = response_content.split(
                    "```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split(
                    "```")[1].split("```")[0].strip()

            feedback_data = json.loads(response_content)

            state["feedback"] = feedback_data.get("feedback", "")
            state["goal_met"] = feedback_data.get("goal_met", False)
            
            # Store next step suggestion for better workflow
            if not state["goal_met"]:
                state["next_step_needed"] = feedback_data.get("next_step_needed", "")

            if state["goal_met"]:
                state["final_answer"] = feedback_data.get("final_answer", "")

            print(f"Feedback: {state['feedback']}")
            print(f"Goal met: {state['goal_met']}")
            if not state["goal_met"] and feedback_data.get("next_step_needed"):
                print(f"Next step needed: {feedback_data.get('next_step_needed')}")

            # Force completion if max iterations reached
            if state["iterations"] >= max_iterations and not state["goal_met"]:
                state[
                    "final_answer"] = f"I wasn't able to fully answer your question within the iteration limit ({max_iterations} iterations), but here's what I found: {state['action_result']}"
                state["goal_met"] = True

        except Exception as e:
            print(f"Error parsing feedback response: {e}")

            # Improved fallback logic
            if action_name == "run_python" and action_result and not action_result.startswith("Error"):
                state["feedback"] = "Successfully executed calculation"
                state["goal_met"] = True
                state["final_answer"] = f"The answer to '{query}' is: {action_result}"
            elif action_name == "search_web" and action_result and "Web Search Results" in action_result:
                # If we got search results, the task is complete - preserve ALL the content
                state["feedback"] = "Successfully retrieved comprehensive web search results with detailed information"
                state["goal_met"] = True
                # Preserve the FULL detailed search results without any summarization
                state["final_answer"] = action_result  # Use the full action_result directly
            elif action_name == "draft_email" and action_result and not action_result.startswith("Error"):
                state["feedback"] = "Email draft created successfully, but not yet sent"
                state["goal_met"] = False  # Draft is not the final goal for email sending
                state["next_step_needed"] = "Review the draft and send the email if satisfied"
            elif action_name == "send_email" and "successfully sent" in action_result.lower():
                state["feedback"] = "Email sent successfully"
                state["goal_met"] = True
                state["final_answer"] = action_result
            else:
                state["feedback"] = str(feedback_result.content)
                state["goal_met"] = False

                if state["iterations"] >= max_iterations:
                    # Preserve full detail even when hitting iteration limit
                    state["final_answer"] = f"I reached the iteration limit ({max_iterations} iterations), but here's the detailed information I found:\n\n{state['action_result']}"
                    state["goal_met"] = True

        return state

    @staticmethod
    def human_confirmation_node(state: AgentState) -> AgentState:
        """
        Handle human-in-the-loop confirmation for sensitive actions.

        This node presents actions to the user for approval before execution.
        """
        print("\n👤 HUMAN CONFIRMATION PHASE")

        action_name = state.get("action_name", "")
        action_input = state.get("action_input", "")
        draft_content = state.get("draft_content", "")

        if action_name in HUMAN_CONFIRMATION_TOOLS:
            tool_config = HUMAN_CONFIRMATION_TOOLS[action_name]
            print(f"\n{tool_config['confirmation_message']}")
            print("=" * 50)

            if draft_content:
                print(draft_content)
            else:
                print(f"Action: {action_name}")
                print(f"Input: {action_input}")

            print("\nOptions:")
            print("  [y/yes] - Confirm and proceed")
            print("  [n/no]  - Cancel this action")
            print("  [m/modify] - Modify the content")
            print("=" * 50)

            try:
                user_input = input("\nYour choice: ").strip().lower()
                state["user_confirmation"] = user_input

                if user_input in ['y', 'yes']:
                    print("✅ Action confirmed by user")
                    # Execute the action immediately after confirmation
                    tools = {
                        "run_python": PythonExecutor.run_python,
                        "send_email": EmailManager.send_gmail,
                        "draft_email": EmailManager.draft_email,
                        "search_web": SearchManager.search_web,
                    }

                    if action_name in tools:
                        try:
                            start_time = time.time()
                            result = tools[action_name](action_input)
                            elapsed = time.time() - start_time

                            state["action_result"] = str(result)
                            print(
                                f"Action completed in {elapsed:.2f}s: {action_name}")
                            print(f"Result: {str(result)[:200]}...")

                            # Mark as completed
                            state["goal_met"] = True
                            state["final_answer"] = f"Action completed successfully: {result}"

                        except Exception as e:
                            state["action_result"] = f"Error executing {action_name}: {str(e)}"
                            state["goal_met"] = True
                            state["final_answer"] = f"Error occurred: {str(e)}"
                            print(f"Action error: {e}")
                    else:
                        state["action_result"] = f"Unknown action: {action_name}"
                        state["goal_met"] = True
                        state["final_answer"] = f"Error: Unknown action {action_name}"

                    state["confirmation_pending"] = False
                    state["needs_confirmation"] = False

                elif user_input in ['n', 'no']:
                    print("❌ Action cancelled by user")
                    state["action_result"] = "Action cancelled by user"
                    state["goal_met"] = True
                    state["final_answer"] = "Action was cancelled at your request."
                    state["confirmation_pending"] = False
                    state["needs_confirmation"] = False
                elif user_input in ['m', 'modify']:
                    print("✏️ Modification requested")
                    # Handle email modification
                    if action_name == "send_email":
                        print("Please provide new email details:")
                        try:
                            new_to = input("To (email address): ").strip()
                            new_subject = input("Subject: ").strip()
                            new_body = input("Body: ").strip()

                            if new_to:
                                modified_input = f"to:{new_to}|subject:{new_subject}|body:{new_body}"
                                # Execute with modified input
                                result = EmailManager.send_gmail(
                                    modified_input)
                                state["action_result"] = str(result)
                                state["goal_met"] = True
                                state["final_answer"] = f"Modified email sent: {result}"
                                print(f"✅ {result}")
                            else:
                                state["action_result"] = "Modification cancelled - no email provided"
                                state["goal_met"] = True
                                state["final_answer"] = "Email modification was cancelled."
                        except KeyboardInterrupt:
                            print("\n❌ Modification cancelled")
                            state["action_result"] = "Modification cancelled"
                            state["goal_met"] = True
                            state["final_answer"] = "Email modification was cancelled."

                    state["confirmation_pending"] = False
                    state["needs_confirmation"] = False
                else:
                    print("❓ Invalid input, treating as cancellation")
                    state["action_result"] = "Invalid confirmation input, action cancelled"
                    state["goal_met"] = True
                    state["final_answer"] = "Action was cancelled due to invalid input."
                    state["confirmation_pending"] = False
                    state["needs_confirmation"] = False

            except KeyboardInterrupt:
                print("\n❌ Action cancelled by user (Ctrl+C)")
                state["action_result"] = "Action cancelled by user"
                state["goal_met"] = True
                state["final_answer"] = "Action was cancelled."
                state["confirmation_pending"] = False
                state["needs_confirmation"] = False
            except Exception as e:
                print(f"❌ Error getting user input: {e}")
                state["action_result"] = f"Error getting user confirmation: {e}"
                state["goal_met"] = True
                state["final_answer"] = "Action was cancelled due to an error."
                state["confirmation_pending"] = False
                state["needs_confirmation"] = False
        else:
            # No confirmation needed
            state["confirmation_pending"] = False
            state["needs_confirmation"] = False

        return state


# ============================================================================
# WORKFLOW ROUTING
# ============================================================================

class WorkflowRouting:
    """Contains routing logic for the workflow graph."""

    @staticmethod
    def should_continue(state: AgentState) -> str:
        """Determine if the agent should continue or end."""
        max_iterations = state.get("max_iterations", 5)
        if state.get("goal_met", False) or state.get("iterations", 0) >= max_iterations:
            return END
        else:
            return "perception_node"

    @staticmethod
    def should_confirm(state: AgentState) -> str:
        """Determine if human confirmation is needed."""
        needs_confirmation = state.get("needs_confirmation", False)
        confirmation_pending = state.get("confirmation_pending", False)

        if needs_confirmation and confirmation_pending:
            return "human_confirmation_node"
        else:
            return "continue_flow"


# ============================================================================
# AGENT CREATION AND EXECUTION
# ============================================================================

class StructuredAgent:
    """Main agent class that orchestrates the entire workflow."""

    @staticmethod
    def create_agent() -> StateGraph:
        """
        Create and configure the agent workflow graph.

        Returns:
            Compiled StateGraph ready for execution
        """
        # Initialize the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("perception_node", WorkflowNodes.perception_node)
        workflow.add_node("reasoning_node", WorkflowNodes.reasoning_node)
        workflow.add_node("action_node", WorkflowNodes.action_node)
        workflow.add_node("feedback_node", WorkflowNodes.feedback_node)
        workflow.add_node("human_confirmation_node",
                          WorkflowNodes.human_confirmation_node)

        # Add edges
        workflow.add_edge("perception_node", "reasoning_node")
        workflow.add_edge("reasoning_node", "action_node")
        workflow.add_edge("action_node", "feedback_node")

        # Add conditional edge from feedback
        workflow.add_conditional_edges(
            "feedback_node",
            WorkflowRouting.should_confirm,
            {
                "human_confirmation_node": "human_confirmation_node",
                "continue_flow": "continue_flow_node"
            }
        )

        # Add continue flow node
        def continue_flow_node(state: AgentState) -> AgentState:
            """Dummy node to handle flow continuation."""
            return state

        workflow.add_node("continue_flow_node", continue_flow_node)

        # Add conditional edges from both confirmation and continue flow nodes
        workflow.add_conditional_edges(
            "human_confirmation_node",
            WorkflowRouting.should_continue,
            {
                END: END,
                "perception_node": "perception_node"
            }
        )

        workflow.add_conditional_edges(
            "continue_flow_node",
            WorkflowRouting.should_continue,
            {
                END: END,
                "perception_node": "perception_node"
            }
        )

        # Set entry point
        workflow.set_entry_point("perception_node")

        return workflow.compile()

    @staticmethod
    def run_agent(query: str, max_iterations: int = 10, timeout: int = 120) -> Dict[str, Any]:
        """
        Run the agent with a specific query.

        Args:
            query: User's input query
            max_iterations: Maximum number of iterations allowed
            timeout: Timeout in seconds

        Returns:
            Dictionary containing the final result
        """
        # Create agent
        agent = StructuredAgent.create_agent()

        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "iterations": 0,
            "goal_met": False,
            "max_iterations": max_iterations,
            "needs_confirmation": False,
            "confirmation_pending": False,
        }

        # Calculate recursion limit
        langgraph_recursion_limit = max_iterations * 4 + 10

        # Run the agent
        try:
            result = agent.invoke(
                initial_state,
                {"recursion_limit": langgraph_recursion_limit, "timeout": timeout}
            )
            return result
        except Exception as e:
            print(f"Error running agent: {e}")
            return {
                "query": query,
                "error": str(e),
                "final_answer": "I encountered an error while processing your request."
            }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point for the structured agent."""
    import sys

    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "Calculate 25 * 8 + 15"

    print(f"\n🚀 Running structured agent with query: {query}")

    # Run the agent
    result = StructuredAgent.run_agent(query)

    # Display results
    print("\n=== FINAL RESULT ===")
    if "final_answer" in result:
        print(f"\n{result['final_answer']}")
    else:
        print(f"\nNo final answer produced. Raw result:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
