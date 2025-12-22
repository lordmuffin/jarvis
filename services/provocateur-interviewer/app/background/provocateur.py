import asyncio
import os
import time
from pathlib import Path
from app.core.gemini import GeminiService
from app.core.messaging import MessagingService

class ProvocateurWorker:
    def __init__(self):
        self.vault_path = os.getenv("KNOWLEDGE_VAULT_PATH", "/data/knowledge-vault")
        self.gemini = GeminiService()
        self.messaging = MessagingService()
        self.running = False
        self.check_interval = 3600  # Check every hour

    async def start(self):
        self.running = True
        print(f"Provocateur worker started. Vault path: {self.vault_path}")
        while self.running:
            await self.process_vault()
            await asyncio.sleep(self.check_interval)

    async def stop(self):
        self.running = False
        await self.messaging.close()

    async def process_vault(self):
        print("Scanning vault for stale notes...")
        try:
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = Path(root) / file
                        if self.is_stale(file_path):
                            print(f"Found stale note: {file}")
                            await self.process_note(file_path)
                            # Rate limit to avoid blasting API
                            await asyncio.sleep(5) 
        except Exception as e:
            print(f"Error processing vault: {e}")

    def is_stale(self, file_path: Path, days: int = 30) -> bool:
        # Check if file hasn't been modified in 'days'
        stats = file_path.stat()
        mtime = stats.st_mtime
        now = time.time()
        return (now - mtime) > (days * 86400)

    async def process_note(self, file_path: Path):
        try:
            content = file_path.read_text(encoding="utf-8")
            if len(content) < 100: # Skip empty/short notes
                return

            # Provocateur Prompt
            prompt = (
                f"You are 'The Provocateur', a critical thinker designed to challenge assumptions.\n"
                f"Analyze the following note from the user's knowledge vault:\n\n"
                f"---\n{content}\n---\n\n"
                f"Identify 1-2 'knowledge gaps', ambiguous statements, or areas that lack depth.\n"
                f"Ask a provocative, open-ended question that forces the user to expand on this topic.\n"
                f"Return ONLY the question."
            )

            question = await self.gemini.generate_content(prompt)
            if question:
                print(f"Generated question for {file_path.name}: {question}")
                
                # Publish to NATS
                payload = f"{file_path.name}|{question}".encode("utf-8")
                await self.messaging.publish("provocateur.questions", payload)

        except Exception as e:
            print(f"Error processing note {file_path}: {e}")

provocateur = ProvocateurWorker()

async def start_worker():
    await provocateur.start()
