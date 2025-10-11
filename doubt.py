from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os



genai.configure(api_key="AIzaSyCaPfJcJ208bDGD54DWZYp4Bw0K4CzsagA")
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "").strip()
    if not question:
        return JSONResponse(content={"answer": "No question provided."})

    response = model.generate_content(question)
    answer = response.text.strip() if hasattr(response, "text") else str(response)
    return JSONResponse(content={"answer": answer})
