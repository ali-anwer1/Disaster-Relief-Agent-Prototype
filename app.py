import streamlit as st
import pandas as pd
import os
import urllib.parse
import io
from google import genai
from google.genai import types

# Load the system prompt from the agent file or define it here
from agent import SYSTEM_PROMPT

def init_agent(api_key):
    """Initializes the Gemini agent with the provided API key."""
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        
    client = genai.Client()
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,  
    )
    
    return client, config

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
    st.header("🧠 Model Selection")
    selected_model = st.selectbox(
        "Choose an AI Model:",
        [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite"
        ],
        index=0,
        help="Select a different model if the current one is experiencing high demand or quota limits."
    )

    st.markdown("---")
    st.header("📲 Output Formats")
    st.info("You can now choose between a WhatsApp-ready message, a strictly formatted CSV table, or both.")

# Main area
mode_col, input_col = st.columns([1, 2])

with mode_col:
    st.subheader("1. Select Settings")
    mode_selection = st.radio(
        "Operation Mode:",
        ["MATCH RESOURCES", "DEPLOY VOLUNTEERS"],
        help="Select the exact trigger phrase required by the agent."
    )
    
    st.markdown("---")
    output_format = st.radio(
        "Output Format:",
        ["WhatsApp Message", "CSV Table", "Both (WhatsApp + CSV)"],
        help="Choose the desired format for the agent's output."
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
                client, config = init_agent(api_key_input)
                
                # Determine format tag
                format_tag = ""
                if output_format == "WhatsApp Message":
                    format_tag = "[FORMAT: WHATSAPP]"
                elif output_format == "CSV Table":
                    format_tag = "[FORMAT: CSV]"
                elif output_format == "Both (WhatsApp + CSV)":
                    format_tag = "[FORMAT: BOTH]"

                # Combine the strict trigger phrase with the user's data and format tag
                full_prompt = f"{mode_selection}:\n\n{user_data}\n\n{format_tag}"
                
                response = client.models.generate_content(
                    model=selected_model,
                    contents=full_prompt,
                    config=config
                )
                
                st.session_state['last_response'] = response.text
                st.session_state['last_format'] = output_format
                st.success("Analysis Complete!")
                
            except Exception as e:
                st.error(f"Error communicating with Gemini: {e}")

# Helper for rendering WhatsApp button
def render_whatsapp_button(text):
    encoded_text = urllib.parse.quote(text)
    whatsapp_url = f"https://wa.me/?text={encoded_text}"
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
                margin-top: 10px;
                margin-bottom: 20px;
            ">
                💬 Share to WhatsApp
            </button>
        </a>
        ''',
        unsafe_allow_html=True
    )

# Display Output
if 'last_response' in st.session_state:
    st.markdown("---")
    st.subheader("📋 Agent Output")
    
    response_text = st.session_state['last_response']
    used_format = st.session_state.get('last_format', "WhatsApp Message")
    
    if used_format == "WhatsApp Message":
        st.text_area("WhatsApp Message (Copy directly):", response_text, height=300)
        render_whatsapp_button(response_text)
        
    elif used_format == "CSV Table":
        st.text_area("Raw CSV Data:", response_text, height=200)
        try:
            # Attempt to render CSV as a dataframe for visualization
            df_out = pd.read_csv(io.StringIO(response_text))
            st.dataframe(df_out, use_container_width=True)
        except Exception as e:
            st.warning("Could not render CSV as a table. Please check the raw data above.")
            
        st.download_button(
            label="📥 Download as CSV",
            data=response_text,
            file_name="nadma_coordination_plan.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    elif used_format == "Both (WhatsApp + CSV)":
        if "---CSV_START---" in response_text:
            parts = response_text.split("---CSV_START---")
            whatsapp_part = parts[0].strip()
            csv_part = parts[1].strip() if len(parts) > 1 else ""
            
            st.markdown("#### WhatsApp Message")
            st.text_area("Copy directly:", whatsapp_part, height=250)
            render_whatsapp_button(whatsapp_part)
            
            st.markdown("#### CSV Data")
            try:
                df_out = pd.read_csv(io.StringIO(csv_part))
                st.dataframe(df_out, use_container_width=True)
            except Exception as e:
                st.text_area("Raw CSV (Render failed):", csv_part, height=150)
                
            st.download_button(
                label="📥 Download CSV File",
                data=csv_part,
                file_name="nadma_coordination_plan.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            # Fallback if the agent failed to use the exact delimiter
            st.warning("Agent failed to separate the formats clearly. Here is the raw output:")
            st.text_area("Raw Output:", response_text, height=400)
