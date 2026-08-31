from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

import config
import database
import rag_engine

app = FastAPI(title="Migraine RAG API")

# CORS - مفتوح في وضع التطوير عشان الفرونت اند (على بورت تاني) يقدر يكلم الباك اند
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# بيسمح للفرونت إند إنه يفتح ملف الـ PDF مباشرة عبر: http://localhost:8000/files/source.pdf
app.mount("/files", StaticFiles(directory=str(config.DATA_DIR)), name="files")


@app.on_event("startup")
def on_startup():
    database.init_db()


class QuestionRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class NewConversationRequest(BaseModel):
    title: str = "محادثة جديدة"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/pdf-info")
def pdf_info():
    return {"filename": config.PDF_FILENAME, "source_label": config.SOURCE_LABEL}

@app.get("/api/evaluation")
def get_evaluation():
    eval_path = config.BASE_DIR / "evaluation_results.json"
    if not eval_path.exists():
        raise HTTPException(
            status_code=404,
            detail="لسه معملتيش تقييم. شغلي 'python evaluate.py' الأول.",
        )
    with open(eval_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/conversations")
def create_conversation(payload: NewConversationRequest):
    conversation_id = database.create_conversation(payload.title)
    return {"id": conversation_id, "title": payload.title}


@app.get("/api/conversations")
def get_conversations():
    return database.list_conversations()


@app.get("/api/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int):
    if not database.conversation_exists(conversation_id):
        raise HTTPException(status_code=404, detail="المحادثة دي مش موجودة")

    raw_messages = database.get_messages(conversation_id)
    messages = []
    for m in raw_messages:
        if m["role"] == "user":
            messages.append({"role": "user", "text": m["content"]})
        else:
            result = json.loads(m["result_json"]) if m["result_json"] else {}
            messages.append({"role": "assistant", "result": result, "messageId": m["id"]})
    return messages


@app.get("/api/retrievals/{message_id}")
def get_message_retrievals(message_id: int):
    raw = database.get_retrievals_for_message(message_id)
    for r in raw:
        r["match_percent"] = round((1 - r["distance"]) * 100)
    return raw


@app.get("/api/retrievals")
def get_all_retrievals():
    return database.get_all_retrievals()


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    if not database.conversation_exists(conversation_id):
        raise HTTPException(status_code=404, detail="المحادثة دي مش موجودة")
    database.delete_conversation(conversation_id)
    return {"deleted": True}


@app.post("/api/query")
def query(payload: QuestionRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="السؤال فاضي")

    conversation_id = payload.conversation_id
    if conversation_id is None:
        title = question[:50]
        conversation_id = database.create_conversation(title)

    # بنسجل رسالة اليوزر ورسالة placeholder للـ assistant الأول، عشان ناخد الـ message_id
    # ونقدر نربط بيه سجل الاسترجاع (retrieval log) من جوه answer_question
    database.add_message(conversation_id, "user", question)
    assistant_message_id = database.add_message(conversation_id, "assistant", question, None)

    try:
        result = rag_engine.answer_question(question, message_id=assistant_message_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # دلوقتي نحدّث رسالة الـ assistant بالنتيجة الحقيقية بدل الـ placeholder
    database.update_message_result(assistant_message_id, json.dumps(result, ensure_ascii=False))

    result["conversation_id"] = conversation_id
    result["assistant_message_id"] = assistant_message_id
    return result