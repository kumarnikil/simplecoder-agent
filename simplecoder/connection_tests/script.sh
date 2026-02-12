# Copy the FULL key from Google AI Studio
export GEMINI_API_KEY="AIzaSyAgb_gzstFhdYLL5QN2LQv6e12sPJVfvwY"

# Verify it's set
echo $GEMINI_API_KEY

# Use project venv so we have google-genai (run from simplecoder/)
python test_api_lite_llm.py
python test_api_sdk.py