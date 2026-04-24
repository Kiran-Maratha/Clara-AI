import os
import logging
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

ai_logger = logging.getLogger('ai_logger')

_client = None

# Initializes the Gemini API client using the environment's security key.
def initialize_gemini():
    global _client
    if _client:
        return _client
        
    api_key = os.getenv('GEMINI_TEXT_PROCESSING_API_KEY')
    if not api_key:
        ai_logger.error("GEMINI API Key not found in environment!")
        return None
        
    _client = genai.Client(api_key=api_key)
    return _client

# Translates multimodal user input and chat history into a structured JSON intent format.
def analyze_request(prompt, media=None, issue_context="General IT Support", chat_history_text=""):
    client = initialize_gemini()
    if not client:
        return None
        
    understanding_model = 'gemini-3.1-flash-lite-preview'
    
    system_instruction = """
    You are an analytical intent engine. Your sole purpose is to read the user's input, extract what they want, and produce STRICT JSON. Do not output anything except the JSON payload.
    Format your JSON exactly like this:
    {
        "intent": "Brief categorized description of what the user wants (e.g. Code Review, System Troubleshooting, General Inquiry)",
        "core_questions": ["Question 1", "Question 2"],
        "extracted_context": "Any specific details, constraints, code snippets, or parameters the user provided.",
        "media_context": "If any images were provided, summarize what they depict."
    }
    """
    
    contents = [
        "CHAT HISTORY FOR CONTEXT:",
        chat_history_text if chat_history_text else "No previous history.",
        f"ISSUE CATEGORY: {issue_context}\nUSER INPUT:", 
        prompt
    ]

    uploaded_files = []
    if media and isinstance(media, list):
        for file_path in media:
            try:
                if os.path.exists(file_path):
                    uploaded_file = client.files.upload(file=file_path)
                    
                    max_retries = 10
                    while uploaded_file.state.name == 'PROCESSING' and max_retries > 0:
                        time.sleep(2)
                        uploaded_file = client.files.get(name=uploaded_file.name)
                        max_retries -= 1
                    
                    if uploaded_file.state.name == 'FAILED':
                        ai_logger.error(f"Media processing failed for {file_path}")
                        continue
                        
                    uploaded_files.append(uploaded_file)
            except Exception as e:
                ai_logger.error(f"Failed to upload media {file_path}: {str(e)}")
                
    if uploaded_files:
        contents.extend(uploaded_files)
        
    try:
        response = client.models.generate_content(
            model=understanding_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return response.text
    except Exception as e:
        ai_logger.error(f"Bot 1 Analysis Failed: {str(e)}")
        return None

# Formulates a professional markdown response based on analyzed user intent and conversation history.
def generate_response(structured_json, chat_history_text=""):
    client = initialize_gemini()
    if not client:
        return "sorry ai currently offline, please check in later...."
        
    answer_model = 'gemini-3.1-flash-lite-preview'
    
    # Load Admin Knowledge Base Files
    knowledge_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'knowledge_base')
    knowledge_context = ""
    if os.path.exists(knowledge_dir):
        for filename in os.listdir(knowledge_dir):
            file_path = os.path.join(knowledge_dir, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        knowledge_context += f"\n--- Admin Knowledge: {filename} ---\n{f.read()}\n"
                except Exception as e:
                    ai_logger.error(f"Failed to read knowledge base file {filename}: {e}")

    kb_section = f"\n\nADMIN KNOWLEDGE BASE DIRECTIVES:\n{knowledge_context}" if knowledge_context else ""

    system_instruction = f"""
    You are Clara AI, your personal IT Support Chatbot.
    You answer intelligently, professionally, and succinctly in markdown format. 
    You have been provided with the user's analyzed intent via JSON natively. 
    Use this JSON explicitly to target their needs gracefully. Do NOT mention that you received JSON or were passed data from another bot.{kb_section}
    
    CHAT HISTORY:
    {chat_history_text if chat_history_text else 'No previous history.'}
    """
    
    contents = ["STRUCTURED USER DATA TO FULFILL:", structured_json]
    
    try:
        response = client.models.generate_content(
            model=answer_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    )
                ]
            )
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        ai_logger.error(f"Bot 2 Generation Failed: {error_msg}")
        if "RESOURCE_EXHAUSTED" in error_msg:
            return f"RESOURCE_EXHAUSTED: {error_msg}"
        return "sorry ai currently offline, please check in later...."
