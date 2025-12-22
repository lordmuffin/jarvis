from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.gemini import GeminiService
from app.core.qdrant import QdrantService
from app.core.messaging import MessagingService

router = APIRouter()

gemini_service = GeminiService()
qdrant_service = QdrantService()
messaging_service = MessagingService()

@router.websocket("/ws/interview")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Session state
    chat_history = []
    
    SYSTEM_PROMPT = (
        "You are 'The Journalist', a sharp, inquisitive interviewer. "
        "Your goal is to extract 'Lessons Learned' from the user. "
        "Challenge vague statements. Ask for specific examples. "
        "Do not be polite; be professional and rigorous. "
        "Use the provided context to point out contradictions or ask for connections."
    )

    try:
        await websocket.send_text("Connected to Real-Time Interviewer. What lesson would you like to discuss today?")
        
        while True:
            data = await websocket.receive_text()
            
            if data.lower() in ["/stop", "/finish", "/summarize"]:
                # Trigger Handoff
                await websocket.send_text("Summarizing session and preparing GitPulse handoff...")
                summary = await summarize_session(chat_history)
                await trigger_gitpulse(summary)
                await websocket.send_text(f"Session Summarized:\n{summary}\n\nGitPulse event triggered. Connection closing.")
                break

            # 1. RAG Retrieve
            # Retrieve relevant notes from Qdrant based on user input
            # assuming we have a collection "knowledge-vault"
            # In a real scenario, we'd embed the query first.
            # For this MVP, we will skip embedding generation here or assume Qdrant handles it if configured, 
            # OR we just pass the text if we had a hybrid search.
            # To keep it simple and runnable without a full embedding service running:
            # We will search based on a mock vector or skip RAG if embedding is missing.
            
            # context_points = await qdrant_service.search("knowledge-vault", [0.1]*768, limit=3) 
            # context_text = "\n".join([p.payload.get('content', '') for p in context_points])
            context_text = "No prior context available for this MVP session."

            # 2. Construct Prompt with Context + History
            # Simple append for history
            chat_history.append(f"User: {data}")
            
            history_text = "\n".join(chat_history[-10:]) # Keep last 10 turns
            
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Context from Vault:\n{context_text}\n\n"
                f"Conversation History:\n{history_text}\n\n"
                f"User: {data}\n"
                f"Journalist:"
            )

            # 3. Generate Response
            response = await gemini_service.generate_content(prompt)
            
            chat_history.append(f"Journalist: {response}")
            await websocket.send_text(response)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in websocket session: {e}")
        await websocket.close()

async def summarize_session(history: list[str]) -> str:
    transcript = "\n".join(history)
    prompt = (
        f"Synthesize the following interview transcript into a structured 'Lessons Learned' markdown note.\n"
        f"Include a Title, Context, key Takeaways, and Actionable Items.\n\n"
        f"Transcript:\n{transcript}"
    )
    return await gemini_service.generate_content(prompt)

async def trigger_gitpulse(summary: str):
    # Publish to NATS for GitPulse service (MS3)
    subject = "gitpulse.create_pr"
    payload = summary.encode("utf-8")
    await messaging_service.publish(subject, payload)
    print("Published to gitpulse.create_pr")
