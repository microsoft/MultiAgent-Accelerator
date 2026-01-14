import streamlit as st
import requests
import json
from datetime import datetime
import time
import os
import ast

# Configuration - use environment variable or default
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://4.150.144.45")

def parse_agent_response(result_str, agent_name):
    """
    Parse agent response and extract clean text based on agent type
    
    Args:
        result_str: The result string from the orchestrator (can be string or dict)
        agent_name: Name of the agent that processed the task
        
    Returns:
        Formatted string for display
    """
    # For travel agent and other simple responses, return as-is if it's a string
    if "burger" not in agent_name.lower() and "pizza" not in agent_name.lower():
        if isinstance(result_str, str):
            return result_str
        return str(result_str)
    
    # For burger/pizza agents (A2A SDK format), parse the nested structure
    try:
        result_dict = None
        
        # Handle if it's already a dict
        if isinstance(result_str, dict):
            result_dict = result_str
        # Handle if it's a string representation of a dict
        elif isinstance(result_str, str):
            # First, try to evaluate it as Python literal
            try:
                result_dict = ast.literal_eval(result_str)
            except:
                # If that fails, try JSON parsing with quote replacement
                try:
                    json_str = result_str.replace("'", '"')
                    result_dict = json.loads(json_str)
                except:
                    # Return original if we can't parse
                    return result_str
        
        # Now extract the text from the parsed dict
        if result_dict:
            # Path: result -> result -> artifacts -> [0] -> parts -> [0] -> text
            if 'result' in result_dict:
                inner_result = result_dict['result']
                
                if isinstance(inner_result, dict) and 'result' in inner_result:
                    task_result = inner_result['result']
                    
                    if isinstance(task_result, dict) and 'artifacts' in task_result:
                        artifacts = task_result['artifacts']
                        
                        if isinstance(artifacts, list) and len(artifacts) > 0:
                            artifact = artifacts[0]
                            
                            if isinstance(artifact, dict) and 'parts' in artifact:
                                parts = artifact['parts']
                                
                                if isinstance(parts, list) and len(parts) > 0:
                                    part = parts[0]
                                    
                                    if isinstance(part, dict) and 'text' in part:
                                        return part['text']
        
        # If we couldn't extract text, return the original
        return str(result_str)
        
    except Exception as e:
        # If any error occurs, return the original string
        return str(result_str)

st.set_page_config(
    page_title="Multi-Agent Orchestrator",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
    }
    .skill-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        background-color: #e3f2fd;
        font-size: 0.875rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 Multi-Agent System")
    st.markdown("### Settings")
    orchestrator_url = st.text_input("Orchestrator URL", value=ORCHESTRATOR_URL)
    user_id = st.text_input("User ID", value="streamlit-user")
    
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("Go to:", ["🏠 Dashboard", "📝 Submit Task", "📊 Monitor Tasks", "🔍 Async Responses"])

# Main content
st.title("Multi-Agent Orchestrator Dashboard")

if page == "🏠 Dashboard":
    st.markdown("## Discovered Agents")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Agents", use_container_width=True):
            st.rerun()
    
    try:
        response = requests.get(f"{orchestrator_url}/agents", timeout=5)
        if response.status_code == 200:
            agents_data = response.json()
            total_agents = agents_data.get("total_agents", 0)
            agents = agents_data.get("agents", [])
            
            st.success(f"✅ Found {total_agents} active agent(s)")
            
            # Display agents
            for agent in agents:
                with st.expander(f"🤖 {agent['name']}", expanded=True):
                    st.markdown(f"**Description:** {agent.get('description', 'No description')}")
                    
                    skills = agent.get('skills', [])
                    if skills:
                        st.markdown("**Skills:**")
                        for skill in skills:
                            skill_name = skill.get('name', 'Unnamed Skill')
                            skill_desc = skill.get('description', 'No description')
                            st.markdown(f"- **{skill_name}**: {skill_desc}")
                    
                    # Show agent metadata
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if '_discovery_url' in agent:
                            st.caption(f"🔗 Discovery: {agent['_discovery_url']}")
                    with col_b:
                        if '_base_url' in agent:
                            st.caption(f"🌐 Base URL: {agent['_base_url']}")
        else:
            st.error(f"❌ Failed to fetch agents: {response.status_code}")
            st.code(response.text)
    except Exception as e:
        st.error(f"❌ Error connecting to orchestrator: {str(e)}")

elif page == "📝 Submit Task":
    st.markdown("## Submit a New Task")
    
    # Quick test buttons
    st.markdown("### 🚀 Quick Test Buttons")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    quick_task = None
    with col_q1:
        if st.button("🍔 Order Burgers", use_container_width=True):
            quick_task = "I want 2 classic cheeseburgers"
    with col_q2:
        if st.button("🍕 Order Pizza", use_container_width=True):
            quick_task = "Order 1 pepperoni pizza"
    with col_q3:
        if st.button("💱 Convert Currency", use_container_width=True):
            quick_task = "Convert 100 USD to EUR"
    with col_q4:
        if st.button("✈️ Plan Trip", use_container_width=True):
            quick_task = "Plan a 3-day trip to Paris"
    
    st.markdown("---")
    
    # Follow-up question buttons (shown after initial response)
    if "show_followups" in st.session_state and st.session_state.show_followups:
        st.markdown("### 💬 Follow-up Questions")
        
        followup_task = None
        
        # Currency & Travel follow-ups
        if st.session_state.get("last_agent_type") in ["travel", "currency", "trip"]:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                if st.button("🏨 Find Hotels", use_container_width=True):
                    followup_task = "Find affordable hotels in Paris"
            with col_f2:
                if st.button("🍽️ Restaurant Recommendations", use_container_width=True):
                    followup_task = "Recommend restaurants in Tokyo"
            with col_f3:
                if st.button("🎭 Tourist Attractions", use_container_width=True):
                    followup_task = "What are the top attractions in Rome?"
        
        # Food order follow-ups
        elif st.session_state.get("last_agent_type") in ["burger", "pizza"]:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                if st.button("🍔 More Burgers", use_container_width=True):
                    followup_task = "Add 3 bacon burgers to my order"
            with col_f2:
                if st.button("🍕 More Pizza", use_container_width=True):
                    followup_task = "Order 2 margherita pizzas"
            with col_f3:
                if st.button("🥤 Add Drinks", use_container_width=True):
                    followup_task = "Can I add drinks to my order?"
        
        if followup_task:
            st.session_state.task_input_value = followup_task
            st.rerun()
        
        st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Use quick_task if button was clicked, otherwise keep the existing value
        default_value = quick_task if quick_task else ""
        if "task_input_value" not in st.session_state:
            st.session_state.task_input_value = default_value
        if quick_task:
            st.session_state.task_input_value = quick_task
            
        task_input = st.text_area(
            "Task Description",
            value=st.session_state.task_input_value,
            placeholder="Example: Create an illustration of a soccer stadium at sunset",
            height=100,
            key="task_description"
        )
    
    with col2:
        execution_mode = st.radio("Execution Mode:", ["Synchronous", "Asynchronous"])
        preferred_agent = st.text_input("Preferred Agent (optional)", placeholder="Leave empty for auto-selection")
    
    col_submit, col_clear = st.columns([1, 1])
    
    with col_submit:
        submit_button = st.button("🚀 Submit Task", use_container_width=True, type="primary")
    
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()
    
    if submit_button and task_input:
        with st.spinner("Processing task..."):
            try:
                endpoint = "/task" if execution_mode == "Synchronous" else "/task/async"
                payload = {
                    "task": task_input,
                    "user_id": user_id
                }
                if preferred_agent:
                    payload["preferred_agent"] = preferred_agent
                
                response = requests.post(
                    f"{orchestrator_url}{endpoint}",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success("✅ Task submitted successfully!")
                    
                    if execution_mode == "Synchronous":
                        # Show raw response in expander
                        with st.expander("🔍 View Raw Response", expanded=False):
                            st.json(result)
                        
                        # Display result nicely
                        if "result" in result:
                            agent_used = result.get("agent_used", "unknown")
                            
                            st.markdown("### 🤖 Agent Response:")
                            
                            # Parse and format the response based on agent type
                            formatted_response = parse_agent_response(result["result"], agent_used)
                            
                            # Display with appropriate icon
                            if "burger" in agent_used.lower():
                                st.success(f"🍔 **{formatted_response}**")
                                st.session_state.last_agent_type = "burger"
                            elif "pizza" in agent_used.lower():
                                st.success(f"🍕 **{formatted_response}**")
                                st.session_state.last_agent_type = "pizza"
                            elif "travel" in agent_used.lower():
                                st.info(formatted_response)
                                # Determine if it's currency or trip planning
                                if "convert" in task_input.lower() or "exchange" in task_input.lower() or "usd" in task_input.lower() or "eur" in task_input.lower():
                                    st.session_state.last_agent_type = "currency"
                                else:
                                    st.session_state.last_agent_type = "travel"
                            else:
                                st.info(formatted_response)
                                st.session_state.last_agent_type = "other"
                            
                            # Show which agent processed it
                            st.caption(f"✨ Processed by: **{agent_used}**")
                            
                            # Enable follow-up questions
                            st.session_state.show_followups = True
                    else:
                        st.markdown("### Message ID:")
                        message_id = result.get("message_id", "N/A")
                        st.code(message_id)
                        
                        # Show additional info
                        if "queue" in result:
                            st.caption(f"📬 Queue: {result['queue']}")
                        if "status" in result:
                            st.caption(f"📊 Status: {result['status']}")
                        
                        st.info("� Check 'Async Responses' page to view the result when ready")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box'>", unsafe_allow_html=True)
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)
                    st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Request failed: {str(e)}")

elif page == "📊 Monitor Tasks":
    st.markdown("## Task Monitoring")
    
    st.info("🚧 Coming soon: Real-time task monitoring and execution logs")
    
    # Example tasks section
    with st.expander("📝 Example Tasks to Try"):
        st.markdown("""
        ### For Travel Agent:
        - "Convert 100 USD to EUR"
        - "Find restaurants in Tokyo"
        - "Plan a 3-day trip to Paris"
        - "Find tourist attractions in New York"
        
        ### For Burger Agent:
        - "I want 2 classic cheeseburgers"
        - "Order 3 bacon burgers"
        
        ### For Pizza Agent:
        - "Order 1 pepperoni pizza"
        - "I want 2 margherita pizzas"
        """)

elif page == "🔍 Async Responses":
    st.markdown("## Async Task Responses")
    
    st.info("💡 **Tip:** Async tasks are processed in the background. Responses appear here when ready.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_filter = st.text_input("Filter by User ID (or 'all' for all users):", value=user_id)
    with col2:
        max_msgs = st.number_input("Max messages:", min_value=1, max_value=50, value=10)
    
    if st.button("🔄 Fetch Responses", use_container_width=True, type="primary"):
        with st.spinner("Fetching responses from Service Bus..."):
            try:
                response = requests.get(
                    f"{orchestrator_url}/responses/{user_filter}",
                    params={"max_messages": max_msgs},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    responses = data.get("responses", [])
                    
                    if total > 0:
                        st.success(f"✅ Found {total} response(s)")
                        
                        for idx, resp in enumerate(responses, 1):
                            with st.expander(f"📬 Response {idx}/{total} - {resp.get('user_id', 'unknown')}", expanded=True):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.caption(f"👤 User: {resp.get('user_id', 'N/A')}")
                                    st.caption(f"🤖 Agent: {resp.get('agent_used', 'N/A')}")
                                with col_b:
                                    st.caption(f"🕐 Time: {resp.get('timestamp', 'N/A')}")
                                    st.caption(f"🆔 Message: {resp.get('message_id', 'N/A')}")
                                
                                st.markdown("**Response:**")
                                st.info(resp.get('response', 'No response'))
                    else:
                        st.warning("📭 No responses found in the queue")
                else:
                    st.error(f"❌ Error: {response.status_code}")
                    st.code(response.text)
                    
            except Exception as e:
                st.error(f"❌ Failed to fetch responses: {str(e)}")
    
    # Note: This would require an endpoint to fetch async responses
    # For now, show instructions
    st.markdown("""
    ### How to view async responses:
    
    1. **Via Kubernetes Job** (current method):
       ```bash
       bash scripts/view-async-responses.sh
       ```
    
    2. **Future enhancement**: Add a `/responses/{user_id}` endpoint to the orchestrator
       to fetch responses directly from the Service Bus queue
    """)
    
    with st.expander("📋 Sample Response Format"):
        st.json({
            "task_id": "abc123",
            "user_id": "streamlit-user",
            "result": "100 USD is approximately 86.42 EUR",
            "timestamp": datetime.now().isoformat(),
            "agent_used": "travel_agent"
        })

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    st.caption("🏗️ Built with Streamlit")
with col_footer2:
    st.caption("🤖 Multi-Agent A2A System")
with col_footer3:
    st.caption(f"🔗 Orchestrator: {orchestrator_url}")
