const API_BASE = "http://localhost:8000";

export async function askQuestion(question, conversationId = null) {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
  if (!res.ok) {
    throw new Error("حصل خطأ في السيرفر");
  }
  return res.json();
}

export async function createConversation(title = "محادثة جديدة") {
  const res = await fetch(`${API_BASE}/api/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    throw new Error("حصل خطأ في إنشاء المحادثة");
  }
  return res.json();
}

export async function listConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`);
  if (!res.ok) {
    throw new Error("حصل خطأ في جلب المحادثات");
  }
  return res.json();
}

export async function getConversationMessages(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`);
  if (!res.ok) {
    throw new Error("حصل خطأ في جلب رسايل المحادثة");
  }
  return res.json();
}

export async function deleteConversation(conversationId) {
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error("حصل خطأ في حذف المحادثة");
  }
  return res.json();
}

export function getPdfUrl(filename) {
  return `${API_BASE}/files/${filename}`;
}

export const API_BASE_URL = API_BASE;

export async function getEvaluation() {
  const res = await fetch(`${API_BASE}/api/evaluation`);
  if (!res.ok) {
    throw new Error("لسه معملتيش تقييم أو حصل خطأ في جلب النتائج");
  }
  return res.json();
}

export async function getMessageRetrievals(messageId) {
  const res = await fetch(`${API_BASE}/api/retrievals/${messageId}`);
  if (!res.ok) {
    throw new Error("حصل خطأ في جلب تفاصيل الاسترجاع");
  }
  return res.json();
}