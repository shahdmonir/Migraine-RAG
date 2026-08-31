import { useEffect, useRef, useState } from "react";
import { ArrowUp, Brain, ShieldCheck } from "lucide-react";
import { askQuestion, getPdfUrl, API_BASE_URL, getConversationMessages } from "../api.js";
import { UserBubble, AnswerBubble } from "./MessageBubble.jsx";
import Loader from "./Loader.jsx";
import { useApp } from "../AppContext.jsx";

export default function ChatWindow({ conversationId, onConversationCreated }) {
  const { t } = useApp();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pdfFilename, setPdfFilename] = useState("source.pdf");
  const bottomRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/pdf-info`)
      .then((r) => r.json())
      .then((d) => setPdfFilename(d.filename))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (conversationId === null) {
      setMessages([]);
      return;
    }
    getConversationMessages(conversationId)
      .then((data) => {
        const marked = data.map((m) => ({ ...m, isHistorical: true }));
        setMessages(marked);
      })
      .catch(() => setMessages([]));
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (question) => {
    const q = question.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoading(true);

    try {
      const result = await askQuestion(q, conversationId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", result, messageId: result.assistant_message_id },
      ]);

      if (conversationId === null && result.conversation_id) {
        onConversationCreated(result.conversation_id);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          result: {
            has_answer: false,
            answer: t.connectionError,
            confidence: "Low",
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-wrap">
      {messages.length === 0 && (
        <div className="empty-state">
          <div className="hero-icon">
            <Brain size={24} />
          </div>
          <span className="eyebrow">{t.heroEyebrow}</span>
          <h1>{t.heroTitle}</h1>
          <p>{t.heroSubtitle}</p>
          <span className="trust-badge">
            <ShieldCheck size={14} />
            {t.trustBadge}
          </span>
          <div className="suggestion-row">
            {t.suggestions.map((s) => (
              <button
                key={s}
                className="suggestion-chip"
                onClick={() => send(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="messages">
        {messages.map((m, idx) =>
          m.role === "user" ? (
            <UserBubble key={idx} text={m.text} />
          ) : (
            <AnswerBubble
              key={idx}
              result={m.result}
              pdfFilename={pdfFilename}
              skipAnimation={m.isHistorical}
              messageId={m.messageId}
            />
          )
        )}
        {loading && <Loader />}
        <div ref={bottomRef} />
      </div>

      <div className="composer-wrap">
        <div className="composer">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder={t.placeholder}
          />
          <button
            className="send-btn"
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}