from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from final_chatbot import query_chatbot
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Azure Chatbot API",
    description="Ask logistics questions via Azure AI Search + OpenAI",
    version="1.0.0"
)

# Enable CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/ask", summary="Ask a logistics question")
async def ask_question(request: QueryRequest):
    try:
        answer = query_chatbot(request.question)
        if answer is None:
            raise HTTPException(status_code=500, detail="Bot failed to respond.")
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))