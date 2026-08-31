# Migraine RAG — دليل التشغيل

مشروع RAG كامل (Backend بايثون + Frontend React) بيجاوب على أسئلة عن الصداع
النصفي بالاعتماد فقط على دليل NICE CG150، ومعاه رابط "Source" بيفتح الملف
الأصلي ويحدد مكان الإجابة بالظبط.

---

## 0) المتطلبات قبل ما تبدئي

- Python 3.10+ مثبت
- Node.js 18+ مثبت (عشان الفرونت اند)
- API key من https://console.anthropic.com (سجلي حساب واعملي key من صفحة API Keys)

---

## 1) حطي ملف الـ PDF

نزّلي ملف NICE CG150 من الرابط ده:
https://www.nice.org.uk/guidance/cg150/resources/headaches-in-over-12s-diagnosis-and-management-pdf-35109624582853

وسميه `source.pdf` وحطيه هنا بالظبط:
```
backend/data/source.pdf
```

---

## 2) شغّلي الـ Backend

افتحي Terminal جوه Visual Studio Code، وادخلي على مجلد backend:

```bash
cd backend
python -m venv venv
```

فعّلي الـ virtual environment:
- ويندوز: `venv\Scripts\activate`
- ماك/لينكس: `source venv/bin/activate`

بعدين ثبتي المكتبات:
```bash
pip install -r requirements.txt
```

انسخي ملف `.env.example` وسميه `.env`، وحطي فيه الـ API key بتاعك:
```bash
cp .env.example .env
```
افتحي `.env` وحطي المفتاح مكان `your_api_key_here`.

**شغّلي التجهيز (مرة واحدة بس، أو كل ما تغيّري الـ PDF):**
```bash
python ingest.py
```
ده هياخد دقيقة لأنه بيحمّل الـ embedding model أول مرة.

**شغّلي السيرفر:**
```bash
uvicorn main:app --reload --port 8000
```

لو شغال هتشوفي: `Uvicorn running on http://127.0.0.1:8000`

---

## 3) شغّلي الـ Frontend

افتحي Terminal تاني (سيبي بتاع الـ backend شغال)، وادخلي على مجلد frontend:

```bash
cd frontend
npm install
npm run dev
```

هيديكي رابط زي: `http://localhost:5173` — افتحيه في المتصفح.

---

## 4) جربي

- اكتبي سؤال عن الصداع النصفي
- هتيجي الإجابة مع badge لدرجة الثقة
- دوسي على زرار "Source" — هيفتحلك تاب جديد فيه الصفحة بالظبط من الـ PDF
  مع تظليل (highlight) الجزء اللي الإجابة طلعت منه

---

## ملاحظات مهمة

- لو غيّرتي الـ PDF، لازم تشغلي `python ingest.py` تاني عشان يعيد بناء قاعدة البيانات.
- الموديل المستخدم هو `claude-sonnet-5` — تقدري تغيريه من ملف `.env`.
- الـ embeddings شغالة محلي على جهازك (مجاناً) — مش محتاجة API key ليها.
- لو ظهرلك خطأ CORS، اتأكدي إن الـ backend شغال على بورت 8000 بالظبط.
