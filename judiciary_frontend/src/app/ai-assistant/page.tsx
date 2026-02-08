"use client";

import { useState, useEffect, useRef } from "react";
import { aiAPI } from "@/lib/api";
import type { ChatMessage, ChatSessionSummary, AIResponse } from "@/types";
import {
  FiSend,
  FiPlus,
  FiTrash2,
  FiMessageSquare,
  FiGlobe,
  FiClock,
  FiZap,
} from "react-icons/fi";

export default function AIAssistantPage() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [language, setLanguage] = useState("auto");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSessions() {
    try {
      const res = await aiAPI.sessions();
      setSessions(res.data.sessions || []);
    } catch {
      // User may not be logged in
    }
  }

  async function loadSession(sessionId: string) {
    try {
      const res = await aiAPI.getSession(sessionId);
      setCurrentSessionId(sessionId);
      setMessages(res.data.session.messages || []);
      setSuggestions([]);
    } catch {
      console.error("Failed to load session");
    }
  }

  function startNewChat() {
    setCurrentSessionId(null);
    setMessages([]);
    setSuggestions([
      "What are bail laws in Pakistan?",
      "Tell me about property disputes",
      "How to file a writ petition?",
      "Explain family law in Pakistan",
    ]);
  }

  async function sendMessage(text?: string) {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setInput("");
    setSuggestions([]);

    // Add user message to UI immediately
    const userMsg: ChatMessage = {
      role: "user",
      content: msg,
      language: "en",
      citations: [],
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await aiAPI.chat({
        message: msg,
        session_id: currentSessionId || undefined,
        language,
      });
      const data: AIResponse = res.data;

      if (!currentSessionId && data.session_id) {
        setCurrentSessionId(data.session_id);
        loadSessions();
      }

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.response,
        language: data.language,
        citations: data.citations || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setSuggestions(data.suggestions || []);
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "I apologize, but I encountered an error. Please make sure you are logged in and try again.",
        language: "en",
        citations: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  async function deleteSession(id: string) {
    try {
      await aiAPI.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        startNewChat();
      }
    } catch {}
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-72" : "w-0"
        } bg-white border-r transition-all duration-300 overflow-hidden flex flex-col`}
      >
        <div className="p-4 border-b">
          <button
            onClick={startNewChat}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            <FiPlus size={16} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer mb-1 ${
                currentSessionId === s.id
                  ? "bg-primary-50 text-primary-700"
                  : "hover:bg-gray-50 text-gray-700"
              }`}
            >
              <FiMessageSquare size={14} className="flex-shrink-0" />
              <button
                onClick={() => loadSession(s.id)}
                className="flex-1 text-left text-sm truncate"
              >
                {s.title}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500"
              >
                <FiTrash2 size={12} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-8">
              No conversations yet
            </p>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <FiMessageSquare size={18} />
            </button>
            <div>
              <h1 className="font-display font-bold text-lg flex items-center gap-2">
                <span className="text-judiciary-gold">⚖</span> Munsif AI
                <span className="text-xs font-normal bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                  AI Legal Assistant
                </span>
              </h1>
              <p className="text-xs text-gray-500 flex items-center gap-2">
                Intelligent Legal Assistant
                <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded text-[10px] font-medium">
                  ✦ Powered by Gemini
                </span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <FiGlobe size={14} className="text-gray-400" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-sm border rounded-lg px-2 py-1"
            >
              <option value="auto">Auto Detect</option>
              <option value="en">English</option>
              <option value="ur">اردو (Urdu)</option>
            </select>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-16">
                <div className="text-6xl mb-4">⚖️</div>
                <h2 className="text-2xl font-display font-bold text-gray-800 mb-2">
                  Welcome to Munsif AI
                </h2>
                <p className="text-gray-500 mb-8 max-w-md mx-auto">
                  Your Intelligent Legal Assistant. Ask me anything
                  about Pakistani law, court cases, or legal procedures.
                </p>
                <div className="grid grid-cols-2 gap-3 max-w-lg mx-auto">
                  {[
                    { icon: <FiZap size={16} />, text: "Case Prediction" },
                    { icon: <FiMessageSquare size={16} />, text: "Legal Research" },
                    { icon: <FiGlobe size={16} />, text: "Bilingual Support" },
                    { icon: <FiClock size={16} />, text: "Case Analysis" },
                  ].map((f) => (
                    <div
                      key={f.text}
                      className="flex items-center gap-2 p-3 bg-white rounded-lg border text-sm text-gray-600"
                    >
                      <span className="text-primary-600">{f.icon}</span>
                      {f.text}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-primary-600 text-white"
                      : "bg-white border shadow-sm"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <p className="text-xs text-primary-600 font-semibold mb-1">
                      ⚖ Munsif AI
                    </p>
                  )}
                  <div
                    className={`text-sm whitespace-pre-wrap ${
                      msg.role === "user" ? "" : "prose prose-sm max-w-none"
                    }`}
                    style={msg.language === "ur" ? { direction: "rtl", textAlign: "right" } : {}}
                  >
                    {msg.content.split("\n").map((line, j) => {
                      // Basic markdown-like rendering
                      if (line.startsWith("## "))
                        return <h3 key={j} className="text-lg font-bold mt-2 mb-1">{line.slice(3)}</h3>;
                      if (line.startsWith("### "))
                        return <h4 key={j} className="text-base font-semibold mt-2 mb-1">{line.slice(4)}</h4>;
                      if (line.startsWith("• ") || line.startsWith("- "))
                        return <p key={j} className="ml-4">{line}</p>;
                      if (line.startsWith("**") && line.endsWith("**"))
                        return <p key={j} className="font-semibold">{line.slice(2, -2)}</p>;
                      return <p key={j}>{line || "\u00A0"}</p>;
                    })}
                  </div>
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-100">
                      <p className="text-xs text-gray-400 mb-1">📋 Referenced Cases:</p>
                      <div className="flex flex-wrap gap-1">
                        {msg.citations.map((cid, ci) => (
                          <a
                            key={ci}
                            href={`/cases/${cid}`}
                            className="text-xs bg-primary-50 text-primary-600 px-2 py-0.5 rounded hover:bg-primary-100 transition"
                          >
                            View Case #{ci + 1}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border shadow-sm rounded-2xl px-4 py-3">
                  <p className="text-xs text-primary-600 font-semibold mb-1">⚖ Munsif AI</p>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="px-4 pb-2">
            <div className="max-w-3xl mx-auto flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-sm px-3 py-1.5 bg-white border rounded-full hover:bg-primary-50 hover:border-primary-200 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t bg-white p-4">
          <div className="max-w-3xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask Munsif AI about Pakistani law..."
              className="input flex-1"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="btn-primary px-4"
            >
              <FiSend size={18} />
            </button>
          </div>
          <p className="max-w-3xl mx-auto text-xs text-gray-400 mt-2 text-center">
            Munsif AI uses Google Gemini AI and your case database to provide legal information. This is not a substitute for professional legal advice.
          </p>
        </div>
      </div>
    </div>
  );
}
