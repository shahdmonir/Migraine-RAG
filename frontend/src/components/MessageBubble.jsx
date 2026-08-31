import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, ListTree } from "lucide-react";
import { useApp } from "../AppContext.jsx";
import { getMessageRetrievals } from "../api.js";

function TypedText({ text, className, skipAnimation }) {
  const [shown, setShown] = useState(skipAnimation ? text : "");

  useEffect(() => {
    if (skipAnimation) {
      setShown(text);
      return;
    }

    setShown("");
    const words = text.split(" ");
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setShown(words.slice(0, i).join(" "));
      if (i >= words.length) clearInterval(interval);
    }, 28);
    return () => clearInterval(interval);
  }, [text, skipAnimation]);

  return <p className={className}>{shown}</p>;
}

export function UserBubble({ text }) {
  return (
    <div className="msg-row user">
      <div className="bubble-user">{text}</div>
    </div>
  );
}

export function AnswerBubble({ result, pdfFilename, skipAnimation, messageId }) {
  const { t, lang } = useApp();
  const { has_answer, answer, confidence, page, snippet, source_label } = result;
  const [showRetrievals, setShowRetrievals] = useState(false);
  const [retrievals, setRetrievals] = useState(null);
  const [loadingRetrievals, setLoadingRetrievals] = useState(false);

  const confidenceLabel = {
    High: t.confidenceHigh,
    Medium: t.confidenceMedium,
    Low: t.confidenceLow,
  };

  const retrievalLabel = lang === "ar" ? "تفاصيل الاسترجاع" : "Retrieval details";
  const matchLabel = lang === "ar" ? "تطابق" : "match";
  const pageLabel = lang === "ar" ? "صفحة" : "page";
  const chunksFoundLabel = lang === "ar" ? "مقاطع اترجعت من البحث" : "chunks retrieved from search";

  const openSource = () => {
    const params = new URLSearchParams({
      page: page,
      snippet: snippet || "",
      file: pdfFilename,
      label: source_label || "",
    });
    window.open(`/source?${params.toString()}`, "_blank");
  };

  const toggleRetrievals = async () => {
    if (!showRetrievals && retrievals === null && messageId) {
      setLoadingRetrievals(true);
      try {
        const data = await getMessageRetrievals(messageId);
        setRetrievals(data);
      } catch (e) {
        setRetrievals([]);
      } finally {
        setLoadingRetrievals(false);
      }
    }
    setShowRetrievals((prev) => !prev);
  };

  return (
    <div className="msg-row">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="answer-card"
      >
        <TypedText
          text={answer}
          className={`answer-text ${!has_answer ? "answer-refusal" : ""}`}
          skipAnimation={skipAnimation}
        />

        {has_answer && (
          <div className="answer-footer">
            <span className={`confidence-badge confidence-${confidence}`}>
              {confidenceLabel[confidence] || confidence}
            </span>

            {page && (
              <button className="source-stub" onClick={openSource}>
                <FileText size={13} />
                {t.source}
                <span className="page-tag">· {t.page}.{page}</span>
              </button>
            )}

            {messageId && (
              <button className="retrieval-stub" onClick={toggleRetrievals}>
                <ListTree size={13} />
                {retrievalLabel}
              </button>
            )}
          </div>
        )}

        {showRetrievals && (
          <div className="retrieval-panel">
            {loadingRetrievals && <span className="retrieval-loading">...</span>}
            {!loadingRetrievals && retrievals && retrievals.length > 0 && (
              <>
                <div className="retrieval-panel-label">
                  {retrievals.length} {chunksFoundLabel}
                </div>
                {retrievals.map((r, idx) => (
                  <div key={idx} className="retrieval-chunk">
                    <div className="retrieval-chunk-header">
                      <span>{pageLabel} {r.page}</span>
                      <span className="retrieval-match">{matchLabel} {r.match_percent}%</span>
                    </div>
                    <p className="retrieval-chunk-text">{r.chunk_text}</p>
                  </div>
                ))}
              </>
            )}
            {!loadingRetrievals && retrievals && retrievals.length === 0 && (
              <span className="retrieval-loading">-</span>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}