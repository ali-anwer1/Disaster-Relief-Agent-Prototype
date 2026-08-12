import streamlit as st
import pandas as pd
import os
import urllib.parse
from google import genai
from google.genai import types

# Load the system prompt from the agent file or define it here
from agent import SYSTEM_PROMPT

def init_agent(api_key):
    """Initializes the Gemini agent with the provided API key."""
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        
    client = genai.Client()
    model_name = "gemini-3.5-flash"  # Using the user's requested model
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,  
    )
    
    return client, model_name, config

def parse_file(uploaded_file):
    """Reads a CSV or Excel file and converts it to a string format."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            return "Error: Unsupported file format."
        
        # Convert the dataframe to a structured markdown/text format for the agent
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error reading file: {e}"

st.set_page_config(
    page_title="NADMA Coordinator Agent",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 NADMA Disaster Coordination Super Agent")
st.markdown("Immediate field actionability and resource/volunteer matching dashboard.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check if API key is in Streamlit secrets
    secret_api_key = st.secrets.get("GEMINI_API_KEY")
    
    if secret_api_key:
        api_key_input = secret_api_key
        st.success("✅ Secure API Key loaded from server secrets.")
    else:
        api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Gemini API Key")
        if not api_key_input:
            st.warning("Please enter your API Key to use the agent.")

    st.markdown("---")
    st.header("📲 Output Formats")
    st.info("The agent strictly outputs WhatsApp-ready formatting (bullets, emojis, no markdown tables) for rapid field deployment.")

# Main area
mode_col, input_col = st.columns([1, 2])

with mode_col:
    st.subheader("1. Select Mode")
    mode_selection = st.radio(
        "Operation Mode:",
        ["MATCH RESOURCES", "DEPLOY VOLUNTEERS"],
        help="Select the exact trigger phrase required by the agent."
    )

with input_col:
    st.subheader("2. Provide Data")
    st.markdown(f"**Trigger Phrase:** `{mode_selection}:`")
    
    input_method = st.radio("Input Method:", ["Paste Text", "Upload File (CSV/Excel)"], horizontal=True)
    
    user_data = ""
    if input_method == "Paste Text":
        user_data = st.text_area("Paste your supply/needs or volunteer/task data here:", height=200)
    else:
        uploaded_files = st.file_uploader("Upload CSV or Excel files", type=['csv', 'xlsx'], accept_multiple_files=True)
        if uploaded_files:
            all_parsed_data = []
            for uploaded_file in uploaded_files:
                parsed_data = parse_file(uploaded_file)
                if parsed_data.startswith("Error"):
                    st.error(f"Error in {uploaded_file.name}: {parsed_data}")
                else:
                    st.success(f"File '{uploaded_file.name}' loaded successfully!")
                    st.expander(f"Preview Extracted Data ({uploaded_file.name})").text(parsed_data)
                    all_parsed_data.append(f"--- Data from {uploaded_file.name} ---\n{parsed_data}")
            user_data = "\n\n".join(all_parsed_data)

    run_agent = st.button("🚀 Run Agent", type="primary", use_container_width=True)

# Processing
if run_agent:
    if not api_key_input:
        st.error("Missing API Key. Please provide it in the sidebar.")
    elif not user_data.strip():
        st.error("Please provide data to process.")
    else:
        with st.spinner("Processing disaster coordination logistics..."):
            try:
                client, model_name, config = init_agent(api_key_input)
                # Combine the strict trigger phrase with the user's data
                full_prompt = f"{mode_selection}:\n\n{user_data}"
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=config
                )
                
                st.session_state['last_response'] = response.text
                st.success("Analysis Complete!")
                
            except Exception as e:
                st.error(f"Error communicating with Gemini: {e}")

# Display Output
if 'last_response' in st.session_state:
    st.markdown("---")
    st.subheader("📋 Agent Output")
    
    # We display the raw text rather than markdown to preserve the exact WhatsApp formatting
    # However, st.markdown handles most of it fine, but we'll use a code block or text area for exact copy-pasting
    
    response_text = st.session_state['last_response']
    st.text_area("Copy directly:", response_text, height=400)
    
    st.markdown("### Export Options")
    col1, col2, _ = st.columns([1, 1, 2])
    
    with col1:
        # Download as TXT
        st.download_button(
            label="📄 Download as Text",
            data=response_text,
            file_name="nadma_coordination_plan.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    with col2:
        # WhatsApp URL encoding
        encoded_text = urllib.parse.quote(response_text)
        whatsapp_url = f"https://wa.me/?text={encoded_text}"
        
        # We use HTML to create a link shaped like a button
        st.markdown(
            f'''
            <a href="{whatsapp_url}" target="_blank" style="text-decoration:none;">
                <button style="
                    background-color:#25D366; 
                    color:white; 
                    border:none; 
                    padding: 0.5rem 1rem; 
                    border-radius: 0.25rem; 
                    cursor:pointer;
                    font-weight:600;
                    width: 100%;
                ">
                    💬 Share to WhatsApp
                </button>
            </a>
            ''',
            unsafe_allow_html=True
        )
