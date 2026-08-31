import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import ChatWindow from "./components/ChatWindow.jsx";
import SourcePage from "./components/SourcePage.jsx";
import TopBar from "./components/TopBar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./components/Dashboard.jsx";
import { useApp } from "./AppContext.jsx";

export default function App() {
  const { lang } = useApp();
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeTab, setActiveTab] = useState("chat");

  const handleNewConversation = () => {
    setActiveConversationId(null);
  };

  const handleSelectConversation = (id) => {
    setActiveConversationId(id);
  };

  const handleConversationCreated = (id) => {
    setActiveConversationId(id);
    setRefreshKey((k) => k + 1);
  };

  const tabLabels = {
    chat: lang === "ar" ? "الشات" : "Chat",
    dashboard: lang === "ar" ? "لوحة التقييم" : "Evaluation dashboard",
  };

  return (
    <Routes>
      <Route
        path="/"
        element={
          <div className="app-shell">
            <Sidebar
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              refreshKey={refreshKey}
            />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", minWidth: 0 }}>
              <TopBar />

              <div className="tab-bar">
                <button
                  className={`tab-item ${activeTab === "chat" ? "active" : ""}`}
                  onClick={() => setActiveTab("chat")}
                >
                  {tabLabels.chat}
                </button>
                <button
                  className={`tab-item ${activeTab === "dashboard" ? "active" : ""}`}
                  onClick={() => setActiveTab("dashboard")}
                >
                  {tabLabels.dashboard}
                </button>
              </div>

              {activeTab === "chat" ? (
                <ChatWindow
                  conversationId={activeConversationId}
                  onConversationCreated={handleConversationCreated}
                />
              ) : (
                <Dashboard />
              )}
            </div>
          </div>
        }
      />
      <Route path="/source" element={<SourcePage />} />
    </Routes>
  );
}