"""
Enhanced Streamlit app for the Environment-Controlled Agent with real-time thinking process visualization.
"""
import os
import time
import json
from typing import Dict, Any, List, Optional
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Import our agent components
from agent import StructuredAgent, AgentState, HUMAN_CONFIRMATION_TOOLS, LLMManager, WorkflowNodes, EmailManager

# Page configuration
st.set_page_config(
    page_title="🤖 Environment-Controlled Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling with animations
st.markdown("""
<style>
    .thinking-container {
        background-color: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .loop-container {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
        border-left: 5px solid #2196f3;
        position: relative;
        animation: slideInLeft 0.6s ease-out;
    }
    
    .step-container {
        background-color: #fafafa;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 3px solid #ff9800;
        animation: fadeIn 0.5s ease-out;
    }
    
    .step-container.perception {
        border-left: 3px solid #9c27b0;
        background: linear-gradient(90deg, #f3e5f5 0%, #fafafa 100%);
    }
    
    .step-container.reasoning {
        border-left: 3px solid #3f51b5;
        background: linear-gradient(90deg, #e8eaf6 0%, #fafafa 100%);
    }
    
    .step-container.action {
        border-left: 3px solid #ff5722;
        background: linear-gradient(90deg, #fbe9e7 0%, #fafafa 100%);
    }
    
    .step-container.feedback {
        border-left: 3px solid #4caf50;
        background: linear-gradient(90deg, #e8f5e9 0%, #fafafa 100%);
    }
    
    .step-container.confirmation {
        border-left: 3px solid #ff9800;
        background: linear-gradient(90deg, #fff3e0 0%, #fafafa 100%);
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-weight: bold;
        font-size: 16px;
    }
    
    .step-icon {
        font-size: 20px;
        margin-right: 10px;
        width: 30px;
        text-align: center;
    }
    
    .step-title {
        color: #2c3e50;
        flex-grow: 1;
    }
    
    .step-time {
        font-size: 11px;
        color: #7f8c8d;
        font-weight: normal;
    }
    
    .thinking-content {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.5;
        border-left: 3px solid #6c757d;
    }
    
    .result-content {
        background-color: #e8f5e9;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
        border-left: 3px solid #4CAF50;
        font-family: monospace;
    }
    
    .error-content {
        background-color: #ffebee;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
        border-left: 3px solid #f44336;
    }
    
    .confirmation-box {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .final-answer {
        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        font-size: 18px;
        font-weight: bold;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
    }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .processing-indicator {
        display: inline-flex;
        align-items: center;
        margin-left: 10px;
    }
    
    .spinner {
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .live-status {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        text-align: center;
        margin: 10px 0;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .loop-header {
        background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px 10px 0 0;
        margin: -20px -20px 15px -20px;
        font-weight: bold;
        font-size: 18px;
    }
    
    .demo-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        margin: 2px;
        cursor: pointer;
        font-size: 12px;
        transition: background-color 0.3s;
    }
    
    .demo-button:hover {
        background-color: #2980b9;
    }
    
    /* Demo prompt button styling */
    .stButton > button {
        width: 100% !important;
        text-align: left !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        height: auto !important;
        min-height: 40px !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        line-height: 1.4 !important;
    }
    
    /* Sidebar expander content styling */
    .streamlit-expanderContent {
        padding-top: 8px !important;
    }
    
    /* Ensure consistent spacing for expander items */
    .streamlit-expanderContent .stButton {
        margin-bottom: 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent_state' not in st.session_state:
    st.session_state.agent_state = {
        'thinking_process': [],
        'is_running': False,
        'result': None,
        'current_loop': 0,
        'current_step': None,
        'confirmation_needed': False,
        'confirmation_data': None,
        'user_response': None,
        'agent_instance': None
    }

if 'demo_prompts' not in st.session_state:
    st.session_state.demo_prompts = {
        "🧮 Math Calculations": [
            "Calculate 25 * 8 + 15",
            "Find the area of a circle with radius 7.5 meters",
            "Calculate compound interest: principal $10,000, annual rate 5%, 3 years",
            "Solve: If I have 24 apples and share them equally among 6 friends, how many does each get?"
        ],
        "📧 Email Tasks": [
            "Send bi-weekly update to Ray",
            "Send an email to john@example.com with subject 'Meeting Reminder' and body 'Don't forget our meeting tomorrow at 2 PM'",
            "Send a thank you email to sarah@company.com",
            "Email my friend at alex@gmail.com to ask how they're doing",
            "Send a birthday greeting to birthday@friend.com"
        ],
        "🌤️ Weather & Location": [
            "What's the current weather in New York?",
            "Weather in Tokyo right now",
            "Current weather conditions in London",
            "What's the temperature in San Francisco?"
        ],
        "💰 Financial Data": [
            "What's the current price of Bitcoin?",
            "Current Tesla stock price",
            "Apple stock price today",
            "What's the price of Ethereum?"
        ],
        "🔍 Specific Information": [
            "What is quantum computing?",
            "Explain the process of photosynthesis",
            "What is the capital of France?",
            "What is the speed of light?"
        ],
        "🎨 Creative Tasks": [
            "Write a haiku about artificial intelligence",
            "Recipe for chocolate cookies for 12 people",
            "Plan a 3-day Tokyo itinerary",
            "What are creative uses for recycled materials?"
        ]
    }

# Extended prompts mapping for full content
if 'extended_prompts' not in st.session_state:
    st.session_state.extended_prompts = {
        "Send bi-weekly update to Ray": """Send an email to my manager Ray (ray.han@sap.com) summarizing my biweekly update for the period from May 5 to May 23. Make sure the email is sent!

Content to include:

**Platform**

Completed:
1. Implemented XL 2.0 file processing backend using CAP within 2 days due to task urgency, paired with platform CoE developer. Followed best CAP practices and implemented current file processing functionality in backend using CAP → works well (File parsing → chunking → Send to Document Grounding)
2. Finalized and set up Renovate bot for automatic dependency upgrades
3. Set up and maintained test and prod environments for XL 2.0:
   - Configured all services on BTP
   - Set up role collection (Access for all SAP employees)
   - Set up important environment variables
   - Implemented CI/CD on Honeycomb
4. Deployed XL 2.0 to test and prod environments and maintained stability

In Progress:
Finalizing stable deployment by end of this week

**CXR:**
1. Conducted 6 CXR-related follow-up calls with CMS team and Sonali's team
2. Per business request, investigated and increased the max_clause number to 2048 in CONTRact Xray, allowing bigger searches with more filters
3. Continuing CXR migration and batch indexing

**Innovation:**
- Working on agent patterns (self-reflection agent and agent thought visualization app)

**Hiring & Mentorship:**
1. Interviewed 2 Accenture candidates and provided feedback"""
    }

class StreamlitAgentRunner:
    """Custom agent runner that integrates with Streamlit for real-time updates"""
    
    def __init__(self):
        self.thinking_process = []
        self.current_loop = 0
        self.confirmation_needed = False
        self.confirmation_data = None
        
    def add_thinking_step(self, loop_num: int, step_name: str, step_icon: str, 
                         thinking: str = "", result: str = "", error: str = "", 
                         status: str = "completed"):
        """Add a thinking step to the process"""
        step_data = {
            'loop': loop_num,
            'step': step_name,
            'icon': step_icon,
        'thinking': thinking,
        'result': result,
        'error': error,
            'status': status,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        self.thinking_process.append(step_data)
        
        # Update session state
        st.session_state.agent_state['thinking_process'] = self.thinking_process
        st.session_state.agent_state['current_step'] = step_name
        st.session_state.agent_state['current_loop'] = loop_num
    
    def request_confirmation(self, action_name: str, action_input: str, draft_content: str = ""):
        """Request user confirmation for an action"""
        self.confirmation_needed = True
        self.confirmation_data = {
            'action_name': action_name,
            'action_input': action_input,
            'draft_content': draft_content,
            'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
        # Update session state
        st.session_state.agent_state['confirmation_needed'] = True
        st.session_state.agent_state['confirmation_data'] = self.confirmation_data
    
    def run_agent_step_by_step(self, query: str, max_iterations: int = 5):
        """Run the agent step by step with Streamlit integration"""
        
        # Initialize state
        state: AgentState = {
            "query": query,
            "iterations": 0,
            "goal_met": False,
            "max_iterations": max_iterations,
            "needs_confirmation": False,
            "confirmation_pending": False,
        }
        
        # Main agent loop
        while not state.get("goal_met", False) and state.get("iterations", 0) < max_iterations:
            loop_num = state.get("iterations", 0) + 1
            self.current_loop = loop_num
            
            # 1. Perception Phase
            self.add_thinking_step(
                loop_num, "Perception", "🔍",
                thinking="Analyzing the query to understand what needs to be done...",
                status="processing"
            )
            
            state = WorkflowNodes.perception_node(state)
            
            self.add_thinking_step(
                loop_num, "Perception", "🔍",
                thinking="Query analysis completed",
                result=state.get("perception", ""),
                status="completed"
            )
            
            # 2. Reasoning Phase
            self.add_thinking_step(
                loop_num, "Reasoning", "🧠",
                thinking="Planning the approach and selecting the best tool for this task...",
                status="processing"
            )
            
            state = WorkflowNodes.reasoning_node(state)
            
            plan_text = f"Selected tool: {state.get('action_name', 'Unknown')}"
            if state.get('action_input'):
                plan_text += f"\nInput: {state.get('action_input', '')}"
            
            self.add_thinking_step(
                loop_num, "Reasoning", "🧠",
                thinking="Tool selection and planning completed",
                result=plan_text,
                status="completed"
            )
            
            # 3. Action Phase
            action_name = state.get("action_name", "")
            
            # Check if confirmation is needed
            if action_name in HUMAN_CONFIRMATION_TOOLS:
                self.add_thinking_step(
                    loop_num, "Action", "🔧",
                    thinking=f"Action '{action_name}' requires user confirmation. Preparing draft...",
                    status="processing"
                )
                
                # Create draft content
                if action_name == "send_email":
                    draft_content = EmailManager.draft_email(state.get("action_input", ""))
                else:
                    draft_content = f"Action: {action_name}\nInput: {state.get('action_input', '')}"
                
                # Request confirmation
                self.request_confirmation(action_name, state.get("action_input", ""), draft_content)
                
                self.add_thinking_step(
                    loop_num, "Action", "🔧",
                    thinking="Waiting for user confirmation...",
                    result="Confirmation required - please check the confirmation section below",
                    status="waiting"
                )
                
                # Return early to wait for user input
                return state, False  # Not completed, waiting for confirmation
            else:
                self.add_thinking_step(
                    loop_num, "Action", "🔧",
                    thinking=f"Executing action: {action_name}",
        status="processing"
    )
    
                state = WorkflowNodes.action_node(state)
                
                self.add_thinking_step(
                    loop_num, "Action", "🔧",
                    thinking="Action execution completed",
                    result=state.get("action_result", ""),
            status="completed"
        )
        
            # 4. Feedback Phase
            self.add_thinking_step(
                loop_num, "Feedback", "📝",
                thinking="Evaluating if the result fully answers the query...",
                status="processing"
            )
            
            state = WorkflowNodes.feedback_node(state)
            
            feedback_result = f"Goal met: {state.get('goal_met', False)}"
            if state.get('feedback'):
                feedback_result += f"\nFeedback: {state.get('feedback', '')}"
            
            self.add_thinking_step(
                loop_num, "Feedback", "📝",
                thinking="Evaluation completed",
                result=feedback_result,
            status="completed"
        )
        
        return state, True  # Completed
    
    def handle_confirmation_response(self, response: str, state: AgentState):
        """Handle user confirmation response"""
        loop_num = state.get("iterations", 0) + 1
        action_name = state.get("action_name", "")
        action_input = state.get("action_input", "")
        
        self.add_thinking_step(
            loop_num, "Confirmation", "👤",
            thinking="Processing user confirmation...",
            status="processing"
        )
        
        try:
            if response == 'confirm':
                # Execute the action
                from agent import PythonExecutor, SearchManager
                
                tools = {
                    "run_python": PythonExecutor.run_python,
                    "send_email": EmailManager.send_gmail,
                    "draft_email": EmailManager.draft_email,
                    "search_web": SearchManager.search_web,
                }
                
                if action_name in tools:
                    try:
                        result = tools[action_name](action_input)
                        state["action_result"] = str(result)
                        state["goal_met"] = True
                        state["final_answer"] = f"Action completed successfully: {result}"
                        
                        self.add_thinking_step(
                            loop_num, "Confirmation", "👤",
                            thinking="User confirmed action. Execution completed.",
                            result=str(result),
                            status="completed"
                        )
                    except Exception as e:
                        state["action_result"] = f"Error executing {action_name}: {str(e)}"
                        state["goal_met"] = True
                        state["final_answer"] = f"Error occurred: {str(e)}"
                        
                        self.add_thinking_step(
                            loop_num, "Confirmation", "👤",
                            thinking="User confirmed action but execution failed.",
                            error=str(e),
                            status="error"
                        )
                else:
                    state["action_result"] = f"Unknown action: {action_name}"
                    state["goal_met"] = True
                    state["final_answer"] = f"Error: Unknown action {action_name}"
                    
                    self.add_thinking_step(
                        loop_num, "Confirmation", "👤",
                        thinking="Unknown action type.",
                        error=f"Unknown action: {action_name}",
                        status="error"
                    )
                    
            elif response == 'cancel':
                state["action_result"] = "Action cancelled by user"
                state["goal_met"] = True
                state["final_answer"] = "Action was cancelled at your request."
                
                self.add_thinking_step(
                    loop_num, "Confirmation", "👤",
                    thinking="User cancelled the action.",
                    result="Action cancelled",
                    status="completed"
                )
                
            elif response.startswith('modify:'):
                # Handle modification
                modified_input = response[7:]  # Remove 'modify:' prefix
                state["action_input"] = modified_input
                
                self.add_thinking_step(
                    loop_num, "Confirmation", "👤",
                    thinking="User modified the input. Re-executing with new parameters...",
                    result=f"Modified input: {modified_input}",
                    status="processing"
                )
                
                # Execute with modified input
                from agent import PythonExecutor, SearchManager
                
                tools = {
                    "run_python": PythonExecutor.run_python,
                    "send_email": EmailManager.send_gmail,
                    "draft_email": EmailManager.draft_email,
                    "search_web": SearchManager.search_web,
                }
                
                if action_name in tools:
                    try:
                        result = tools[action_name](modified_input)
                        state["action_result"] = str(result)
                        state["goal_met"] = True
                        state["final_answer"] = f"Action completed successfully with modifications: {result}"
                        
                        self.add_thinking_step(
                            loop_num, "Confirmation", "👤",
                            thinking="Modified action executed successfully.",
                            result=str(result),
                            status="completed"
                        )
                    except Exception as e:
                        state["action_result"] = f"Error executing modified {action_name}: {str(e)}"
                        state["goal_met"] = True
                        state["final_answer"] = f"Error occurred with modified input: {str(e)}"
                        
                        self.add_thinking_step(
                            loop_num, "Confirmation", "👤",
                            thinking="Modified action execution failed.",
                            error=str(e),
                            status="error"
                        )
                else:
                    state["action_result"] = f"Unknown action: {action_name}"
                    state["goal_met"] = True
                    state["final_answer"] = f"Error: Unknown action {action_name}"
                    
                    self.add_thinking_step(
                        loop_num, "Confirmation", "👤",
                        thinking="Unknown action type for modified input.",
                        error=f"Unknown action: {action_name}",
                        status="error"
                    )
            else:
                # Handle unexpected response
                state["action_result"] = f"Unexpected response: {response}"
                state["goal_met"] = True
                state["final_answer"] = f"Unexpected response received: {response}"
                
                self.add_thinking_step(
                    loop_num, "Confirmation", "👤",
                    thinking="Received unexpected response.",
                    error=f"Unexpected response: {response}",
                    status="error"
                )
        
        except Exception as e:
            # Handle any unexpected errors in confirmation processing
            state["action_result"] = f"Error in confirmation handling: {str(e)}"
            state["goal_met"] = True
            state["final_answer"] = f"Error in confirmation handling: {str(e)}"
            
            self.add_thinking_step(
                loop_num, "Confirmation", "👤",
                thinking="Error occurred during confirmation processing.",
                error=str(e),
                status="error"
            )
        
        # Clear confirmation state
        self.confirmation_needed = False
        self.confirmation_data = None
        st.session_state.agent_state['confirmation_needed'] = False
        st.session_state.agent_state['confirmation_data'] = None
        
        return state

def create_thinking_process_view(thinking_process: List[Dict]):
    """Create a visual representation of the agent's thinking process"""
    
    if not thinking_process:
        st.markdown("""
        <div class="thinking-container">
            <h3>🤖 Agent Thinking Process</h3>
            <p style="color: #7f8c8d; text-align: center; padding: 20px;">
                The agent's thinking process will appear here as it works...
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="thinking-container">', unsafe_allow_html=True)
    st.markdown("### 🤖 Agent Thinking Process")
    
    # Group steps by loop
    loops = {}
    for step in thinking_process:
        loop_num = step['loop']
        if loop_num not in loops:
            loops[loop_num] = []
        loops[loop_num].append(step)
    
    # Display each loop
    for loop_num in sorted(loops.keys()):
        steps = loops[loop_num]
        
        st.markdown(f'<div class="loop-container"><div class="loop-header">🔄 Loop {loop_num}</div>', unsafe_allow_html=True)
        
        # Display steps in this loop
        for step in steps:
            step_name = step['step']
            icon = step['icon']
            thinking = step.get('thinking', '')
            result = step.get('result', '')
            error = step.get('error', '')
            status = step.get('status', 'completed')
            timestamp = step.get('timestamp', '')
        
            # Determine CSS class
            css_class = f"step-container {step_name.lower()}"
            
            # Build status indicators
            status_indicator = ""
            if status == 'processing':
                status_indicator = '<div class="processing-indicator"><div class="spinner"></div>Processing...</div>'
            elif status == 'waiting':
                status_indicator = '<div class="processing-indicator">⏳ Waiting...</div>'
        
            st.markdown(f'<div class="{css_class}"><div class="step-header"><span class="step-icon">{icon}</span><span class="step-title">{step_name}</span><span class="step-time">{timestamp}</span>{status_indicator}</div>', unsafe_allow_html=True)
            
            # Show thinking process
            if thinking:
                st.markdown(f'<div class="thinking-content"><strong>💭 Thinking:</strong><br>{thinking}</div>', unsafe_allow_html=True)
            
            # Show results
            if result:
                st.markdown(f'<div class="result-content"><strong>✅ Result:</strong><br><pre>{result}</pre></div>', unsafe_allow_html=True)
            
            # Show errors
            if error:
                st.markdown(f'<div class="error-content"><strong>❌ Error:</strong><br>{error}</div>', unsafe_allow_html=True)
            
            # Close step container
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Close loop container
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Close thinking container
    st.markdown('</div>', unsafe_allow_html=True)

def handle_confirmation_request(confirmation_data: Dict, agent_runner: StreamlitAgentRunner):
    """Handle user confirmation request with interactive UI"""
    action_name = confirmation_data['action_name']
    action_input = confirmation_data['action_input']
    draft_content = confirmation_data.get('draft_content', '')
    
    st.markdown(f"""
    <div class="confirmation-box">
        <h3>👤 User Confirmation Required</h3>
        <p><strong>Action:</strong> {action_name}</p>
        <p><strong>Time:</strong> {confirmation_data['timestamp']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show draft content
    if draft_content:
        st.markdown("**📋 Draft Content:**")
        st.code(draft_content, language="text")
    else:
        st.markdown(f"**📋 Action Input:** `{action_input}`")
    
    # Create interactive confirmation interface
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✅ Confirm", key="confirm_btn", type="primary"):
            st.session_state.agent_state['user_response'] = 'confirm'
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key="cancel_btn"):
            st.session_state.agent_state['user_response'] = 'cancel'
            st.rerun()
    
    with col3:
        if st.button("✏️ Modify", key="modify_btn"):
            st.session_state.agent_state['show_modify'] = True
            st.rerun()
    
    # Show modification interface if requested
    if st.session_state.agent_state.get('show_modify', False):
        st.markdown("**✏️ Modify the content:**")
        
        try:
            if action_name == "send_email":
                # Parse email data for modification
                parsed = EmailManager.parse_email_data(action_input)
                
                modified_to = st.text_input("To:", value=parsed.get('to', ''), key="mod_to")
                modified_subject = st.text_input("Subject:", value=parsed.get('subject', ''), key="mod_subject")
                modified_body = st.text_area("Body:", value=parsed.get('body', ''), height=100, key="mod_body")
                
                col_mod1, col_mod2 = st.columns([1, 1])
                with col_mod1:
                    if st.button("💾 Save & Confirm", key="save_confirm_btn", type="primary"):
                        if modified_to.strip():  # Ensure we have a valid email
                            modified_input = f"to:{modified_to}|subject:{modified_subject}|body:{modified_body}"
                            st.session_state.agent_state['user_response'] = f'modify:{modified_input}'
                            st.session_state.agent_state['show_modify'] = False
                            st.rerun()
                        else:
                            st.error("Please enter a valid email address")
                
                with col_mod2:
                    if st.button("🚫 Cancel Modify", key="cancel_modify_btn"):
                        st.session_state.agent_state['show_modify'] = False
                        st.rerun()
            else:
                # Generic modification for other actions
                modified_input = st.text_area("Modified Input:", value=action_input, height=100, key="mod_generic")
                
                col_mod1, col_mod2 = st.columns([1, 1])
                with col_mod1:
                    if st.button("💾 Save & Confirm", key="save_confirm_generic_btn", type="primary"):
                        if modified_input.strip():  # Ensure we have valid input
                            st.session_state.agent_state['user_response'] = f'modify:{modified_input}'
                            st.session_state.agent_state['show_modify'] = False
                            st.rerun()
                        else:
                            st.error("Please enter valid input")
                
                with col_mod2:
                    if st.button("🚫 Cancel Modify", key="cancel_modify_generic_btn"):
                        st.session_state.agent_state['show_modify'] = False
                        st.rerun()
        
        except Exception as e:
            st.error(f"Error in modification interface: {str(e)}")
            # Reset modification state on error
            st.session_state.agent_state['show_modify'] = False

def main():
    # Title
    st.title("🤖 Environment-Controlled Agent")
    st.markdown("### *Advanced AI Agent with Real-time Thinking Process & Human in the Loop*")
    
    # Feature introduction with compelling description
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: 20px 0; text-align: center;">
        <h3 style="margin-top: 0; color: white;">🧠 Experience AI That Thinks Out Loud</h3>
        <p style="font-size: 16px; margin-bottom: 15px; color: #f0f0f0;">
            Watch as our advanced AI agent processes your requests with complete transparency
        </p>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin-top: 20px;">
            <div style="flex: 1; min-width: 200px; margin: 10px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                <strong>Real-time Thinking</strong><br>
                <small>See every step of the AI's reasoning process as it happens</small>
            </div>
            <div style="flex: 1; min-width: 200px; margin: 10px;">
                <div style="font-size: 24px; margin-bottom: 8px;">🛠️</div>
                <strong>Smart Tool Selection</strong><br>
                <small>AI intelligently chooses the right tools for each task</small>
            </div>
            <div style="flex: 1; min-width: 200px; margin: 10px;">
                <div style="font-size: 24px; margin-bottom: 8px;">👤</div>
                <strong>Human Control</strong><br>
                <small>Review and approve sensitive actions before execution</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call-to-action for demo prompts
    st.markdown("""
    <div style="background-color: #e8f4fd; border-left: 4px solid #1f77b4; padding: 15px; margin: 15px 0; border-radius: 0 10px 10px 0;">
        <h4 style="margin-top: 0; color: #1f77b4;">🚀 Ready to see it in action?</h4>
        <p style="margin-bottom: 8px; color: #2c5282;">
            <strong>👈 Try the demo prompts in the sidebar!</strong> Click any category to explore:
        </p>
        <div style="margin-left: 20px; color: #2c5282;">
            • 🧮 <strong>Math Calculations</strong> - Watch AI solve complex problems step-by-step<br>
            • 📧 <strong>Email Tasks</strong> - See human-in-the-loop confirmation for sensitive actions<br>
            • 🌤️ <strong>Weather & Location</strong> - Experience intelligent web search with real-time data<br>
            • 💰 <strong>Financial Data</strong> - Get current stock prices and market information<br>
            • 🔍 <strong>Knowledge Queries</strong> - Ask questions and see detailed reasoning<br>
            • 🎨 <strong>Creative Tasks</strong> - Generate content with transparent thinking process
        </div>
        <p style="margin-top: 12px; margin-bottom: 0; color: #1f77b4; font-weight: bold;">
            Each demo showcases different AI capabilities and thinking patterns! 🎯
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.markdown("""
        **🔧 Setup Instructions:**
        1. Copy `env_template.txt` to `.env`
        2. Edit `.env` and add your OpenAI API key
        3. Restart the application
        
        **Or set it temporarily below:**
        """)
        api_key = st.text_input("Enter your OpenAI API key:", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API key has been set!")
            st.rerun()
        return
    
    # Check if .env file exists and provide guidance
    if not os.path.exists('.env') and not os.getenv("OPENAI_API_KEY"):
        st.info("💡 This app uses environment variables for configuration. In Streamlit Cloud, these are set in the app settings under 'Secrets'.")
        with st.expander("🔧 Local Development Setup (Optional)"):
            st.markdown("""
            **For local development only:**
            1. Copy `env_template.txt` to `.env`
            2. Edit `.env` with your actual credentials
            3. Restart the application
            
            **For Streamlit Cloud:** Set your API keys in the app settings → Secrets section.
            """)
    
    # Check Tavily API key (optional but recommended for web search)
    if not os.getenv("TAVILY_API_KEY"):
        with st.expander("🔑 Optional: Web Search Configuration"):
            st.markdown("For enhanced web search functionality, add your Tavily API key in the app settings.")
            st.markdown("Get your free API key at [tavily.com](https://tavily.com)")
            tavily_key = st.text_input("Enter your Tavily API key:", type="password", key="tavily_key")
            if st.button("Set Tavily Key") and tavily_key:
                os.environ["TAVILY_API_KEY"] = tavily_key
                st.success("✅ Tavily API key has been set!")
                st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Demo Prompts")
        
        # Demo prompt categories
        for category, prompts in st.session_state.demo_prompts.items():
            with st.expander(category):
                for prompt in prompts:
                    # Use consistent button styling for all demo prompts
                    button_key = f"demo_{hash(prompt)}"  # Use hash for unique keys
                    if st.button(
                        prompt, 
                        key=button_key, 
                        help=f"Click to use: {prompt}",
                        use_container_width=True  # Make buttons full width for consistency
                    ):
                        # Check if there's an extended version of this prompt
                        extended_prompt = st.session_state.extended_prompts.get(prompt, prompt)
                        st.session_state.selected_prompt = extended_prompt
        
        st.markdown("---")
        
        # Settings
        st.header("⚙️ Settings")
        max_iterations = st.slider("Max Iterations", 1, 10, 5)
        
        st.markdown("---")
        
        # Agent information
        st.header("🤖 Agent Info")
        st.markdown("""
        **Available Tools:**
        - 🐍 Python Calculator
        - 📧 Gmail Email Sender (requires confirmation)
        - 🔍 Web Search (Enhanced with full content)
        
        **Processing Phases:**
        1. 🔍 Perception - Understand the task
        2. 🧠 Reasoning - Choose appropriate tools
        3. 🔧 Action - Execute tools
        4. 📝 Feedback - Evaluate results
        5. 👤 Confirmation - User approval (if needed)
        """)
        
        # Configuration Status
        st.markdown("**📋 Configuration Status:**")
        
        # OpenAI API Key
        if os.getenv("OPENAI_API_KEY"):
            st.success("✅ OpenAI API configured")
        else:
            st.error("❌ OpenAI API key missing")
        
        # Gmail Configuration
        gmail_email = os.getenv("GMAIL_EMAIL", "")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        
        if gmail_email and gmail_email != "your_email@gmail.com" and gmail_password and gmail_password != "your_app_password_here":
            st.success("✅ Gmail configured")
        else:
            st.warning("⚠️ Gmail not configured")
            st.markdown("Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env")
        
        # Tavily API Key
        if os.getenv("TAVILY_API_KEY"):
            st.success("✅ Web search enabled (with full content)")
        else:
            st.warning("⚠️ Web search requires TAVILY_API_KEY")
            st.markdown("Get your free API key at [tavily.com](https://tavily.com)")
    
    # Main content area
    # Query input section
    st.header("💬 Your Query")
    
    # Use selected demo prompt (if any)
    default_query = st.session_state.get('selected_prompt', '')
    query = st.text_area(
        "Enter your query:",
        value=default_query,
        height=100,
        placeholder="e.g., 'Calculate 25 * 8 + 15' or 'Send an email to john@example.com'"
    )
    
    # Control buttons and status in aligned columns
    col_main1, col_main2, col_main3, col_status = st.columns([3, 1, 1, 2])
    
    with col_main1:
        run_button = st.button("🚀 Run Agent", type="primary", disabled=st.session_state.agent_state['is_running'])
    
    with col_main2:
        clear_button = st.button("🗑️ Clear", disabled=st.session_state.agent_state['is_running'])
    
    with col_main3:
        # Empty column for spacing
        pass
    
    with col_status:
        # Live status display
        if st.session_state.agent_state['is_running']:
            current_step = st.session_state.agent_state.get('current_step', 'Processing')
            st.markdown(f"""
            <div style="background: linear-gradient(45deg, #ff6b6b, #4ecdc4); color: white; padding: 8px 12px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; margin: 0;">
                🤖 {current_step}
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.agent_state['confirmation_needed']:
            st.markdown("""
            <div style="background-color: #fff3e0; color: #e65100; padding: 8px 12px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; border: 2px solid #ffcc02;">
                ⏳ Waiting for Confirmation
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.agent_state['result']:
            st.markdown("""
            <div style="background-color: #d4edda; color: #155724; padding: 8px 12px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; border: 2px solid #4caf50;">
                ✅ Complete
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #e2e3e5; color: #495057; padding: 8px 12px; border-radius: 20px; text-align: center; font-weight: bold; font-size: 12px; border: 2px solid #6c757d;">
                ⏳ Ready
            </div>
            """, unsafe_allow_html=True)
    
    # Clear button functionality
    if clear_button:
        st.session_state.agent_state = {
            'thinking_process': [],
            'is_running': False,
            'result': None,
            'current_loop': 0,
            'current_step': None,
            'confirmation_needed': False,
            'confirmation_data': None,
            'user_response': None,
            'agent_instance': None
        }
        if 'selected_prompt' in st.session_state:
            del st.session_state.selected_prompt
        if 'show_modify' in st.session_state:
            del st.session_state.show_modify
        st.rerun()
    
    # Start agent execution
    if run_button and query:
        st.session_state.agent_state.update({
            'thinking_process': [],
            'is_running': True,
            'result': None,
            'current_loop': 0,
            'current_step': 'Starting',
            'confirmation_needed': False,
            'confirmation_data': None,
            'user_response': None
        })
        
        # Create agent runner
        agent_runner = StreamlitAgentRunner()
        st.session_state.agent_state['agent_instance'] = agent_runner
        
        # Run the agent
        try:
            state, completed = agent_runner.run_agent_step_by_step(query, max_iterations)
            
            if completed:
                st.session_state.agent_state['is_running'] = False
                st.session_state.agent_state['result'] = {
                    'final_answer': state.get('final_answer', 'Task completed'),
                    'error': False
                }
            
        except Exception as e:
            st.session_state.agent_state['is_running'] = False
            st.session_state.agent_state['result'] = {
                'final_answer': f'Error: {str(e)}',
                'error': True
            }
        
        st.rerun()
    
    # Handle user confirmation response
    if st.session_state.agent_state.get('user_response') and st.session_state.agent_state.get('agent_instance'):
        response = st.session_state.agent_state['user_response']
        agent_runner = st.session_state.agent_state['agent_instance']
        
        # Get the current state (we'll need to reconstruct it or store it)
        # For simplicity, we'll create a minimal state for confirmation handling
        confirmation_data = st.session_state.agent_state.get('confirmation_data')
        if confirmation_data:
            state = {
                'iterations': st.session_state.agent_state.get('current_loop', 1) - 1,
                'action_name': confirmation_data['action_name'],
                'action_input': confirmation_data['action_input']
            }
            
            try:
                # Handle the response
                final_state = agent_runner.handle_confirmation_response(response, state)
                
                # Update final result
                st.session_state.agent_state['is_running'] = False
                st.session_state.agent_state['result'] = {
                    'final_answer': final_state.get('final_answer', 'Task completed'),
                    'error': 'error' in final_state.get('final_answer', '').lower()
                }
                st.session_state.agent_state['user_response'] = None
                
                if 'show_modify' in st.session_state.agent_state:
                    del st.session_state.agent_state['show_modify']
                
            except Exception as e:
                # Handle any errors in confirmation processing
                st.session_state.agent_state['is_running'] = False
                st.session_state.agent_state['result'] = {
                    'final_answer': f'Error processing confirmation: {str(e)}',
                    'error': True
                }
                st.session_state.agent_state['user_response'] = None
                
                if 'show_modify' in st.session_state.agent_state:
                    del st.session_state.agent_state['show_modify']
        
        st.rerun()
    
    # Handle user confirmation UI
    if st.session_state.agent_state['confirmation_needed'] and st.session_state.agent_state['confirmation_data']:
        agent_runner = st.session_state.agent_state.get('agent_instance')
        if agent_runner:
            handle_confirmation_request(st.session_state.agent_state['confirmation_data'], agent_runner)
    
    # Display thinking process
    thinking_placeholder = st.empty()
    with thinking_placeholder.container():
        create_thinking_process_view(st.session_state.agent_state['thinking_process'])
        
        # Display final answer
    if st.session_state.agent_state['result']:
        result = st.session_state.agent_state['result']
        
        # Auto-scroll to results section
        st.markdown("""
        <script>
        setTimeout(function() {
            const resultsSection = document.querySelector('[data-testid="stMarkdown"]');
            if (resultsSection) {
                const resultsElements = Array.from(document.querySelectorAll('h2')).find(el => el.textContent.includes('Results'));
                if (resultsElements) {
                    resultsElements.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }
        }, 500);
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Results header with anchor
        st.markdown('<a name="results"></a>', unsafe_allow_html=True)
        st.markdown("## 🎯 **Results**")
        
        if not result.get('error', False):
            # Create a dedicated results window with better formatting
            with st.container():
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 10px 10px 0 0;
                    margin-bottom: 0;
                    font-weight: bold;
                    font-size: 18px;
                ">
                    ✅ Task Completed Successfully
                </div>
                """, unsafe_allow_html=True)
                
                # Results content window with scrolling
                results_html = result['final_answer']
                # Improved HTML formatting for better display
                results_html = results_html.replace('\n', '<br>')
                
                # Handle markdown-style formatting
                results_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', results_html)
                results_html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', results_html)
                results_html = re.sub(r'(https?://[^\s<>"]+)', r'<a href="\1" target="_blank">\1</a>', results_html)
                
                st.markdown(f"""
                <div id="results-container" style="
                    background-color: #f8f9fa;
                    border: 2px solid #4caf50;
                    border-top: none;
                    border-radius: 0 0 10px 10px;
                    padding: 20px;
                    max-height: 600px;
                    overflow-y: auto;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    font-size: 14px;
                    animation: fadeInResult 0.8s ease-out;
                ">
                {results_html}
                </div>
                
                <style>
                @keyframes fadeInResult {{
                    from {{
                        opacity: 0;
                        transform: translateY(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # Add copy button and download option
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("📋 Copy Results", key="copy_results"):
                        st.success("Results ready to copy!")
                        st.code(result['final_answer'], language="text")
                
                with col2:
                    # Download results as text file
                    st.download_button(
                        label="💾 Download Results",
                        data=result['final_answer'],
                        file_name="agent_results.txt",
                        mime="text/plain"
                    )
                
                # JavaScript to auto-scroll to results with better targeting
                st.markdown("""
                <script>
                setTimeout(function() {
                    const resultsContainer = document.getElementById('results-container');
                    if (resultsContainer) {
                        resultsContainer.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });
                        // Add a subtle highlight effect
                        resultsContainer.style.boxShadow = '0 0 20px rgba(76, 175, 80, 0.3)';
                        setTimeout(function() {
                            resultsContainer.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                        }, 2000);
                    }
                }, 1000);
                </script>
                """, unsafe_allow_html=True)
        else:
            st.error(f"❌ Agent encountered an error: {result['final_answer']}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Made with ❤️ using LangGraph, LangChain, and Streamlit*")

if __name__ == "__main__":
    main()
 
 