import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Loader2, ShieldCheck, MessageCircle, FileCheck, Link2, Clock, Search } from "lucide-react";
import { getEvaluation } from "../api.js";
import { useApp } from "../AppContext.jsx";

const categoryLabels = {
  in_scope_answerable: { ar: "في النطاق - يُجاب عليه", en: "In scope - answerable" },
  in_scope_not_covered: { ar: "في النطاق - غير مغطى", en: "In scope - not covered" },
  out_of_scope: { ar: "خارج النطاق", en: "Out of scope" },
  unsafe_personal: { ar: "طلب شخصي/جرعة", en: "Personal/dosage request" },
  injection: { ar: "محاولة اختراق", en: "Injection attempt" },
};

export default function Dashboard() {
  const { lang } = useApp();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getEvaluation()
      .then((d) => setData(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const labels = {
    title: lang === "ar" ? "لوحة تقييم النظام" : "System evaluation dashboard",
    safety: lang === "ar" ? "درجة الأمان" : "Safety score",
    answerable: lang === "ar" ? "درجة الإجابة" : "Answerable score",
    citation: lang === "ar" ? "دقة التوثيق" : "Citation accuracy",
    precision: lang === "ar" ? "دقة الاسترجاع" : "Precision@K",    faithfulness: lang === "ar" ? "الالتزام بالمصدر" : "Faithfulness",
    latency: lang === "ar" ? "متوسط زمن الاستجابة" : "Avg latency",
    seconds: lang === "ar" ? "ثانية" : "sec",
    question: lang === "ar" ? "السؤال" : "Question",
    category: lang === "ar" ? "النوع" : "Category",
    result: lang === "ar" ? "النتيجة" : "Result",
    answerLabel: lang === "ar" ? "إجابة" : "answer",
    refuseLabel: lang === "ar" ? "رفض" : "refuse",
    noData: lang === "ar" ? "لسه معملتيش تقييم. شغلي evaluate.py الأول." : "No evaluation yet. Run evaluate.py first.",
  };

  if (loading) {
    return (
      <div className="dashboard-wrap">
        <Loader2 className="spin" size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-wrap">
        <p className="dashboard-error">{labels.noData}</p>
      </div>
    );
  }

  const { metrics, detailed_results } = data;

  const metricCards = [
    { label: labels.latency, value: `${metrics.average_latency_seconds} ${labels.seconds}`, tone: "neutral", icon: Clock },
    { label: labels.precision, value: metrics.precision_at_k, tone: "score", icon: Search },
    { label: labels.faithfulness, value: metrics.faithfulness_approx, tone: "score", icon: Link2 },
    { label: labels.citation, value: metrics.citation_accuracy, tone: "score", icon: FileCheck },
    { label: labels.answerable, value: metrics.answerable_score_only, tone: "score", icon: MessageCircle },
    { label: labels.safety, value: metrics.safety_score_only, tone: "score", icon: ShieldCheck },
  ];

  const getScoreTone = (value) => (value >= 0.9 ? "good" : "warn");

  return (
    <div className="dashboard-wrap">
      <h1 className="dashboard-title">{labels.title}</h1>

      <div className="metric-grid">
        {metricCards.map((m) => {
          const Icon = m.icon;
          const toneClass = m.tone === "neutral" ? "metric-neutral" : `metric-${getScoreTone(m.value)}`;
          const displayValue = m.tone === "neutral" ? m.value : `${Math.round(m.value * 100)}%`;
          return (
            <div className={`metric-card ${toneClass}`} key={m.label}>
              {m.tone !== "neutral" && <Icon size={16} className="metric-icon" />}
              <span className="metric-value">{displayValue}</span>
              <span className="metric-label">{m.label}</span>
            </div>
          );
        })}
      </div>

      <div className="results-table">
        <div className="results-row results-header">
          <span className="col-question">{labels.question}</span>
          <span className="col-category">{labels.category}</span>
          <span className="col-result">{labels.result}</span>
        </div>
        {detailed_results.map((r) => (
          <div className="results-row" key={r.id}>
            <span className="col-question">{r.question}</span>
            <span className="col-category">{categoryLabels[r.category]?.[lang] || r.category}</span>
            <span className="col-result">
              <span className={`result-badge ${r.actual_behavior === "answer" ? "badge-answer" : "badge-refuse"}`}>
                {r.actual_behavior === "answer" ? labels.answerLabel : labels.refuseLabel}
                {r.behavior_correct ? (
                  <CheckCircle2 size={13} />
                ) : (
                  <XCircle size={13} />
                )}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}