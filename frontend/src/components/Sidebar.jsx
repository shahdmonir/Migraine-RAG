import { useEffect, useState } from "react";
import { Plus, Search, Trash2, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { listConversations, deleteConversation } from "../api.js";
import { useApp } from "../AppContext.jsx";

function groupByDate(conversations) {
  const groups = { today: [], yesterday: [], older: [] };
  const now = new Date();
  const todayStr = now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const yesterdayStr = yesterday.toDateString();

  for (const c of conversations) {
    const d = new Date(c.created_at);
    if (d.toDateString() === todayStr) groups.today.push(c);
    else if (d.toDateString() === yesterdayStr) groups.yesterday.push(c);
    else groups.older.push(c);
  }
  return groups;
}

export default function Sidebar({
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  refreshKey,
}) {
  const { lang } = useApp();
  const [conversations, setConversations] = useState([]);
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState(false);

  const loadConversations = async () => {
    try {
      const data = await listConversations();
      setConversations(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [refreshKey]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    const confirmMsg = lang === "ar" ? "متأكدة إنك عايزة تمسحي المحادثة دي؟" : "Delete this conversation?";
    if (!window.confirm(confirmMsg)) return;

    try {
      await deleteConversation(id);
      if (id === activeConversationId) {
        onNewConversation();
      }
      loadConversations();
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );
  const groups = groupByDate(filtered);

  const labels = {
    today: lang === "ar" ? "النهاردة" : "Today",
    yesterday: lang === "ar" ? "إمبارح" : "Yesterday",
    older: lang === "ar" ? "أقدم" : "Older",
    newChat: lang === "ar" ? "محادثة جديدة" : "New chat",
    search: lang === "ar" ? "بحث..." : "Search...",
  };

  if (collapsed) {
    return (
      <div className="sidebar sidebar-collapsed">
        <button className="icon-btn" onClick={() => setCollapsed(false)}>
          <PanelLeftOpen size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Migraine Guide</span>
        <button className="icon-btn-plain" onClick={() => setCollapsed(true)}>
          <PanelLeftClose size={16} />
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewConversation}>
        <Plus size={15} />
        {labels.newChat}
      </button>

      <div className="sidebar-search">
        <Search size={13} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={labels.search}
        />
      </div>

      <div className="sidebar-list">
        {groups.today.length > 0 && (
          <>
            <div className="sidebar-group-label">{labels.today}</div>
            {groups.today.map((c) => (
              <ConversationRow
                key={c.id}
                conv={c}
                active={c.id === activeConversationId}
                onClick={() => onSelectConversation(c.id)}
                onDelete={(e) => handleDelete(e, c.id)}
              />
            ))}
          </>
        )}
        {groups.yesterday.length > 0 && (
          <>
            <div className="sidebar-group-label">{labels.yesterday}</div>
            {groups.yesterday.map((c) => (
              <ConversationRow
                key={c.id}
                conv={c}
                active={c.id === activeConversationId}
                onClick={() => onSelectConversation(c.id)}
                onDelete={(e) => handleDelete(e, c.id)}
              />
            ))}
          </>
        )}
        {groups.older.length > 0 && (
          <>
            <div className="sidebar-group-label">{labels.older}</div>
            {groups.older.map((c) => (
              <ConversationRow
                key={c.id}
                conv={c}
                active={c.id === activeConversationId}
                onClick={() => onSelectConversation(c.id)}
                onDelete={(e) => handleDelete(e, c.id)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function ConversationRow({ conv, active, onClick, onDelete }) {
  return (
    <div
      className={`conversation-row ${active ? "active" : ""}`}
      onClick={onClick}
    >
      <span className="conversation-title">{conv.title}</span>
      <button className="delete-btn" onClick={onDelete}>
        <Trash2 size={13} />
      </button>
    </div>
  );
}