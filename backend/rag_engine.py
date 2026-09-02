import json
import re

import chromadb
from chromadb.utils import embedding_functions
from google import genai

import config
import database

_client = None
_collection = None
_embed_fn = None
_gemini_clients = {}  # هنخزن فيها كل موديل client لكل مفتاح، عشان منعملش تهيئة من جديد كل مرة
_current_key_index = 0  # المفتاح اللي بنستخدمه حالياً

# لو أقرب مقطع مسترجع أبعد من الرقم ده، نعتبر إن مفيش دليل كافي ونرفض من غير ما نكلم الموديل خالص
DISTANCE_THRESHOLD = 0.63

# كلمات ومحاولات شائعة لمحاولة اختراق الـ system prompt (تجاهل التعليمات، كشف الأوامر السرية...)
INJECTION_PATTERNS = [
    r"تجاهل.{0,15}(تعليمات|قواعد|أوامر)",
    r"انسى.{0,15}(تعليمات|قواعد|أوامر)",
    r"(قولي|اديني|اعطيني).{0,15}(رأيك الشخصي|رأيك الخاص)",
    r"ignore.{0,20}(previous|all|above).{0,15}(instructions?|rules?)",
    r"disregard.{0,15}(instructions?|rules?|prompt)",
    r"forget.{0,15}(instructions?|rules?|everything)",
    r"you are now",
    r"act as if",
    r"system prompt",
    r"(اظهر|أظهر|اعرض|قوللي).{0,15}(التعليمات|البرومبت|الأوامر السرية)",
    r"jailbreak",
    r"developer mode",
    r"DAN mode",
]


def _get_collection():
    global _client, _collection, _embed_fn
    if _collection is None:
        if not config.CHROMA_DIR.exists():
            raise RuntimeError(
                "قاعدة البيانات مش موجودة. شغلي 'python ingest.py' الأول."
            )
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        _collection = _client.get_collection(
            name=config.COLLECTION_NAME, embedding_function=_embed_fn
        )
    return _collection


def _get_gemini_client(key_index: int):
    """بترجع Gemini client لمفتاح معين، وبتعمل caching عشان منعيدش التهيئة كل مرة"""
    if key_index not in _gemini_clients:
        if not config.GEMINI_API_KEYS:
            raise RuntimeError("مفيش أي GEMINI_API_KEY_1/2/3 موجود في ملف .env")
        api_key = config.GEMINI_API_KEYS[key_index]
        _gemini_clients[key_index] = genai.Client(api_key=api_key)
    return _gemini_clients[key_index]


def _is_quota_error(exception: Exception) -> bool:
    """بتتأكد هل الخطأ ده بسبب انتهاء الكوتة تحديداً (429 RESOURCE_EXHAUSTED)"""
    error_text = str(exception)
    return "429" in error_text and "RESOURCE_EXHAUSTED" in error_text


SYSTEM_PROMPT = """أنت مساعد طبي متخصص بيجاوب فقط بناءً على المقاطع (context) اللي هتوصلك.

قواعد صارمة:
1. جاوب فقط من المعلومات الموجودة في المقاطع اللي هتديلك. ممنوع تضيف أي معلومة من عندك أو من معرفتك العامة.
2. لو المقاطع مش كافية للإجابة على السؤال، رجّع has_answer = false.
3. جاوب بشكل مباشر وواضح، من غير ما تقول جمل زي "بناءً على الملف" أو "المستند يقول" - جاوبي وكأنك عارفة الإجابة مباشرة.
4. لازم تختاري أهم جزء نصي (snippet) من المقطع اللي اعتمدتي عليه في الإجابة - ده هيتستخدم لتحديد مكانه في الملف الأصلي، فلازم يكون نص مقتبس بالحرف من المقطع (مش بصياغتك) وطوله من 6 لـ 15 كلمة. الـ snippet ده لازم يفضل بنفس لغة المقطع الأصلي دايماً (حتى لو إجابتك بلغة تانية).
5. مهم جداً: جاوبي دايماً بنفس لغة السؤال بالظبط. لو السؤال مكتوب بالإنجليزي، خلي حقل "answer" بالكامل بالإنجليزي (بما فيها حالات الرفض وعدم توفر المعلومة). لو السؤال بالعربي، خلي الإجابة بالعربي.

متى تجاوبي (Allowed) ومتى ترفضي (Refuse):
- أسئلة عامة عن محتوى الدليل (زي "إيه هي أدوية الوقاية؟"، "إيه هي أعراض الصداع النصفي؟"، "إيه الفرق بين X و Y؟") = جاوبي عليها بمعلومة عامة من الدليل، حتى لو كانت عن أدوية أو علاجات. ده معلومة تثقيفية عامة مش قرار سريري لحالة معينة.
- أسئلة فيها سيناريو شخصي أو طلب جرعة محددة (زي "أنا وزني كذا هاخد كام مللي؟"، "أنا حامل، آخد الدواء ده؟"، أي سؤال بيوصف حالة المستخدم الشخصية ويطلب قرار علاجي بناءً عليها) = ارفضي الإجابة وقولي إن ده قرار لازم يتاخد مع طبيب مباشرة (بنفس لغة السؤال).
- لو جاوبتي عن دواء أو علاج بشكل عام، أضيفي في نهاية الإجابة جملة قصيرة (بنفس لغة السؤال) توضح إن القرار النهائي واستخدام أي دواء لازم يكون تحت إشراف طبيب.

6. رجّعي الإجابة بصيغة JSON فقط، من غير أي نص زيادة قبلها أو بعدها. الأمثلة تحت بالعربي بس افتكري إن حقل "answer" لازم يتبع لغة السؤال:

مثال لو السؤال عربي وفيه إجابة:
{
  "has_answer": true,
  "answer": "الإجابة هنا، واضحة ومباشرة",
  "confidence": "High",
  "page": 5,
  "snippet": "النص المقتبس بالحرف من المقطع"
}

لو مفيش إجابة كافية في الدليل (بالعربي كمثال، بالإنجليزي لو السؤال إنجليزي: "There isn't enough information in the guide to answer this. Try asking another migraine-related question."):
{
  "has_answer": false,
  "answer": "مفيش معلومة كافية في الدليل عن السؤال ده. جربي تسألي سؤال تاني متعلق بموضوع الصداع النصفي.",
  "confidence": "Low",
  "page": null,
  "snippet": null
}

لو السؤال فيه سيناريو شخصي أو طلب جرعة (Refuse) (بالعربي كمثال، بالإنجليزي لو السؤال إنجليزي: "This is a personal treatment decision that needs to be made with a specialist doctor. Please ask your doctor or pharmacist."):
{
  "has_answer": false,
  "answer": "ده قرار علاجي شخصي لازم يتاخد مع طبيب متخصص، مش ممكن أقترحه هنا. اسألي طبيبك أو الصيدلي.",
  "confidence": "Low",
  "page": null,
  "snippet": null
}

confidence لازم تكون واحدة من: High, Medium, Low
"""


def _build_context(results):
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    parts = []
    for doc, meta in zip(docs, metas):
        parts.append(f"[صفحة {meta['page']}]\n{doc}")
    return "\n\n---\n\n".join(parts)


def _extract_json(text):
    """بتشيل أي مارك داون كود بلوك لو الموديل حطه بالغلط وترجع الجزء JSON بس"""
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("مقدرتش أستخرج JSON من رد الموديل")


def _is_english(text: str) -> bool:
    return bool(re.search(r"[a-zA-Z]", text)) and not re.search(r"[\u0600-\u06FF]", text)


def _detect_injection(question: str) -> bool:
    """بتكشف محاولات الاختراق (Prompt Injection) قبل ما السؤال يوصل للموديل أصلاً"""
    lowered = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return True
    return False


def _refusal_response(answer_ar: str, answer_en: str, is_english: bool):
    return {
        "has_answer": False,
        "answer": answer_en if is_english else answer_ar,
        "confidence": "Low",
        "page": None,
        "snippet": None,
        "source_label": config.SOURCE_LABEL,
    }


def _chunks_from_results(results):
    """بتحول نتيجة ChromaDB لقايمة dicts سهلة الحفظ في قاعدة البيانات"""
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    chunks = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
        chunks.append({
            "rank": i + 1,
            "text": doc,
            "page": meta.get("page"),
            "distance": dist,
        })
    return chunks


def _generate_with_key_rotation(context: str, question: str):
    """
    بتحاول تولد الإجابة، ولو مفتاح معين رجع 'كوتة خلصت'، بتنتقل تلقائياً للمفتاح اللي بعده.
    بترجع (raw_text) لو نجحت، أو بترفع Exception لو كل المفاتيح فشلوا.
    """
    global _current_key_index

    if not config.GEMINI_API_KEYS:
        raise RuntimeError("مفيش أي GEMINI_API_KEY_1/2/3 موجود في ملف .env")

    num_keys = len(config.GEMINI_API_KEYS)
    last_error = None

    # بنبدأ من المفتاح الحالي، ولو فشل بسبب كوتة، ندور على الباقيين بالترتيب
    for attempt in range(num_keys):
        key_index = (_current_key_index + attempt) % num_keys
        try:
            client = _get_gemini_client(key_index)
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=f"المقاطع المسترجعة:\n\n{context}\n\n---\n\nالسؤال: {question}",
                config={"system_instruction": SYSTEM_PROMPT},
            )
            # نجح! نثبت المفتاح ده كأساسي للمرة الجاية
            _current_key_index = key_index
            return response.text
        except Exception as e:
            last_error = e
            if _is_quota_error(e):
                print(f"مفتاح رقم {key_index + 1} كوتته خلصت، بجرب المفتاح اللي بعده...")
                continue
            else:
                # مشكلة تانية غير الكوتة (زي انقطاع نت) - نرفعها فوراً من غير ما ندور على مفاتيح تانية
                raise

    # لو وصلنا هنا، يبقى كل المفاتيح جربناهم وكلهم كوتتهم خلصت
    raise RuntimeError(
        f"كل مفاتيح الـ API ({num_keys}) وصلوا للحد اليومي المسموح. حاولي تاني بعد شوية."
    ) from last_error


def answer_question(question: str, message_id: int = None):
    is_english = _is_english(question)

    # 1) فحص محاولات الاختراق (Injection) - الرجوع للـ Regex بس حالياً
    if _detect_injection(question):
        if message_id is not None:
            database.add_retrieval_log(
                message_id, question, chunks=[], was_rejected=True, was_injection=True
            )
        return _refusal_response(
            "النظام ده مصمم يجاوب بس من الدليل الطبي المعتمد، ومقدرش أدي آراء شخصية أو أغيّر طريقة عملي. اسألي أي سؤال عن الصداع النصفي وهساعدك.",
            "This system is designed to answer only from the certified medical guideline, and I can't provide personal opinions or change how I work. Feel free to ask anything about migraine.",
            is_english,
        )

    # 2) البحث والاسترجاع (Retrieval)
    collection = _get_collection()
    results = collection.query(
        query_texts=[question],
        n_results=config.TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"][0]:
        if message_id is not None:
            database.add_retrieval_log(message_id, question, chunks=[], was_rejected=True)
        return _refusal_response(
            "مفيش داتا كافية للإجابة على السؤال ده.",
            "There isn't enough data to answer this question.",
            is_english,
        )

    chunks = _chunks_from_results(results)

    # 3) بوابة الثقة (Confidence Threshold) - لو أقرب مقطع بعيد جداً، نرفض من غير ما نكلم الموديل
    closest_distance = min(results["distances"][0])
    print(f"=== أقرب distance: {closest_distance:.4f} (الحد المسموح: {DISTANCE_THRESHOLD}) ===")

    if closest_distance > DISTANCE_THRESHOLD:
        if message_id is not None:
            database.add_retrieval_log(message_id, question, chunks=chunks, was_rejected=True)
        return _refusal_response(
            "السؤال ده مش متعلق بموضوع الصداع النصفي أو مش موجود في الدليل. جربي تسألي سؤال تاني عن الصداع النصفي.",
            "This question doesn't seem related to migraine or isn't covered in the guideline. Try asking something else about migraine.",
            is_english,
        )

    # سجّلي كل الـ chunks اللي رجعت (حتى اللي معتمدهاش الموديل في الإجابة النهائية)
    if message_id is not None:
        database.add_retrieval_log(message_id, question, chunks=chunks, was_rejected=False)

    # 4) توليد الإجابة (Generation) مع المراجع - بتدوير تلقائي بين المفاتيح لو حد منهم كوتته خلصت
    context = _build_context(results)

    try:
        raw_text = _generate_with_key_rotation(context, question)
        parsed = _extract_json(raw_text)
        parsed["source_label"] = config.SOURCE_LABEL
        parsed["retrieved_pages"] = [c["page"] for c in chunks]
        return parsed
    except Exception as e:
        raise RuntimeError(f"فشل الاتصال بالموديل: {e}") from e