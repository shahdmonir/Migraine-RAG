import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { getPdfUrl } from "../api.js";
import { useApp } from "../AppContext.jsx";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.js",
  import.meta.url
).toString();

function normalize(str) {
  return (str || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, "").trim();
}

export default function SourcePage() {
  const { t } = useApp();
  const [params] = useSearchParams();
  const page = parseInt(params.get("page") || "1", 10);
  const snippet = params.get("snippet") || "";
  const file = params.get("file") || "source.pdf";
  const label = params.get("label") || "";

  const [numPages, setNumPages] = useState(null);
  const normalizedSnippet = normalize(snippet);

  const customTextRenderer = (textItem) => {
    const cleanWord = normalize(textItem.str);
    if (
      cleanWord.length > 2 &&
      normalizedSnippet.includes(cleanWord)
    ) {
      return `<mark class="highlight">${textItem.str}</mark>`;
    }
    return textItem.str;
  };

  return (
    <div className="source-page">
      <div className="source-page-header">
        <h2>{label || t.sourcePage}</h2>
        <span className="mono">{t.sourcePage} {page}{numPages ? ` / ${numPages}` : ""}</span>
      </div>

      <div className="pdf-frame">
        <Document
          file={getPdfUrl(file)}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          loading={<div style={{ padding: 40 }}>{t.sourceLoading}</div>}
        >
          <Page
            pageNumber={page}
            width={820}
            customTextRenderer={customTextRenderer}
          />
        </Document>
      </div>
    </div>
  );
}