import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not set")
        else:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_content(self, prompt: str) -> str:
        try:
            response = await self.model.generate_content_async(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            return response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return ""

    async def generate_with_context(self, context: str, prompt: str) -> str:
        full_prompt = f"Context:\n{context}\n\nUser Question:\n{prompt}"
        return await self.generate_content(full_prompt)
