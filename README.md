# Disaster-Relief-Agent-Prototype
Vibecode oblivion
Built entirely using Antigravity IDE and Gemini 3.1 Pro as a test to create an AI agent with a functioning dashboard in a few minutes.
Scrapes through unstructured data in the form of a whatsapp message or a csv file and returns either a whatsapp message or a csv file that either matches resources or volunteers to the desired location with the help of AI.
Uses Gemini to perform these tasks as it is the only mainstream AI that provides free API keys which can be used at least a dozen or so times before it becomes limited.
The dashboard was created using Streamlit and its associated python library as it is a lightweight framework and is simple to use compared to React etc. (at least according to my Antigravity agent).
The agent can also be used directly through a python terminal with agent.py, though if one were to use this program in all its glory then fork this repo and host it with Streamlit (using app.py), share it with your friend if you'd like.
agent.py is primarily used to store the meticulously engineered prompt through the effort of dozens of prompt fine-tuning trials with Claude.
