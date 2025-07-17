from fastapi import  Request, APIRouter
from app.utils.models import ChatRequest


# Initialize FastAPI app
router = APIRouter()

# Store user queries
chat_history_list = []



# Endpoint for chatting
@router.post("/chat")
async def chat(request_chat: Request, request: ChatRequest):
    user_question = request.question
    chat_history_list.append(user_question)  # Track all queries
    response = request_chat.app.state.chat_chain.run(user_question)

    return {
        "question": user_question,
        "answer": response,
        "history": chat_history_list
    }
