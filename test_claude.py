import streamlit as st
import os
from openai import OpenAI

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

st.title("Claude Connection Test")

# Check environment variables
openai_key = os.getenv("OPENAI_API_KEY")
claude_key = os.getenv("ANTHROPIC_API_KEY")

st.write(f"OpenAI Key: {'✅ Found' if openai_key else '❌ Missing'}")
st.write(f"Claude Key: {'✅ Found' if claude_key else '❌ Missing'}")
st.write(f"Anthropic Package: {'✅ Installed' if CLAUDE_AVAILABLE else '❌ Missing'}")

if claude_key and CLAUDE_AVAILABLE:
    try:
        client = anthropic.Anthropic(api_key=claude_key)
        st.success("✅ Claude client created successfully!")
        
        # Test a simple call
        if st.button("Test Claude"):
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say hello!"}]
            )
            st.write("Claude response:", response.content[0].text)
            
    except Exception as e:
        st.error(f"❌ Claude error: {e}")
else:
    st.error("❌ Claude setup incomplete")