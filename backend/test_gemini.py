import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv("backend/.env")

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)