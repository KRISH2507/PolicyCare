import React, {
  useState,
  useContext,
  useRef,
  useEffect,
  useCallback,
} from 'react';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import '../styles/chat.css';

/* ─────────────────────────────────────────────
   Helpers
───────────────────────────────────────────── */

/** Persist chat history to localStorage so it survives a page refresh. */
const STORAGE_KEY = 'aarogyaaid_chat_history';

const loadPersistedHistory = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const persistHistory = (history) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch {
    /* storage quota — silently ignore */
  }
};

/** Build the greeting message shown when the panel first opens. */
const buildGreeting = (userProfile, recommendationResult) => {
  const name = userProfile?.full_name || 'there';
  const policy = recommendationResult?.best_fit?.policy_name || 'your recommended plan';
  return (
    `Hi ${name}, I've recommended ${policy}. ` +
    `Ask me anything about waiting periods, diabetes coverage, claims, ` +
    `co-pay, exclusions, or cheaper alternatives.`
  );
};

/* ─────────────────────────────────────────────
   Sub-components
───────────────────────────────────────────── */

const TypingIndicator = () => (
  <div className="chat-row chat-row--assistant" role="status" aria-label="Assistant is typing">
    <div className="chat-bubble-typing">
      <span>Analyzing your policy</span>
      <div className="chat-typing-dots" aria-hidden="true">
        <span /><span /><span />
      </div>
    </div>
  </div>
);

const MessageRow = ({ msg }) => {
  const isUser = msg.role === 'user';

  return (
    <div className={`chat-row ${isUser ? 'chat-row--user' : 'chat-row--assistant'}`}>
      {isUser ? (
        <div className="chat-bubble-user">{msg.content}</div>
      ) : msg.isError ? (
        <div className="chat-bubble-error">{msg.content}</div>
      ) : (
        <>
          <div className="chat-bubble-assistant">{msg.content}</div>
          {msg.citations && msg.citations.length > 0 && (
            <p className="chat-citation">
              Source: {msg.citations.join(', ')}
            </p>
          )}
        </>
      )}
    </div>
  );
};

/* ─────────────────────────────────────────────
   Main component
───────────────────────────────────────────── */

const ChatPanel = () => {
  const { userProfile, recommendationResult, conversationHistory, setConversationHistory } =
    useContext(SessionContext);

  const greeting = buildGreeting(userProfile, recommendationResult);

  /* ── Initialise messages ──
     Priority: in-memory context → localStorage → fresh greeting */
  const [messages, setMessages] = useState(() => {
    if (conversationHistory && conversationHistory.length > 0) {
      return conversationHistory;
    }
    const persisted = loadPersistedHistory();
    if (persisted && persisted.length > 0) {
      return persisted;
    }
    return [{ role: 'assistant', content: buildGreeting(userProfile, recommendationResult), citations: [] }];
  });

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  /* ── Auto-scroll to bottom on new messages ── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  /* ── Sync messages → context + localStorage ── */
  useEffect(() => {
    setConversationHistory(messages);
    persistHistory(messages);
  }, [messages, setConversationHistory]);

  /* ── Build the history array the backend expects ──
     Only user/assistant turns, no error or greeting metadata */
  const buildApiHistory = useCallback(
    (currentMessages) =>
      currentMessages
        .filter((m) => (m.role === 'user' || m.role === 'assistant') && !m.isError)
        .map((m) => ({ role: m.role, content: m.content })),
    []
  );

  /* ── Send message ── */
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isTyping) return;

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];

    setMessages(nextMessages);
    setInput('');
    setIsTyping(true);

    try {
      const payload = {
        message: text,
        user_profile: userProfile || {},
        recommended_policy_name: recommendationResult?.best_fit?.policy_name || '',
        recommended_policy_id: recommendationResult?.best_fit?.policy_id ?? null,
        history: buildApiHistory(nextMessages),
      };

      const data = await apiPost('/api/chat/', payload);

      const assistantMsg = {
        role: 'assistant',
        content: data.reply || 'No response received.',
        citations: data.citations || [],
        isError: false,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "I couldn't fetch the policy details right now. Please try again.",
          citations: [],
          isError: true,
        },
      ]);
    } finally {
      setIsTyping(false);
      // Return focus to input after response
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, isTyping, messages, userProfile, recommendationResult, buildApiHistory]);

  /* ── Keyboard handler ── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const canSend = input.trim().length > 0 && !isTyping;

  return (
    <div className="chat-panel" role="region" aria-label="Policy chat assistant">
      {/* Header */}
      <div className="chat-header">
        <p className="chat-header-title">Ask about this plan</p>
        <p className="chat-header-sub">Answers based on uploaded policy documents</p>
        <div className="chat-header-divider" aria-hidden="true" />
      </div>

      {/* Messages */}
      <div
        className="chat-messages"
        role="log"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.map((msg, i) => (
          <MessageRow key={i} msg={msg} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} aria-hidden="true" />
      </div>

      {/* Input */}
      <div className="chat-input-wrap">
        <input
          ref={inputRef}
          className="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about waiting periods, diabetes cover, claims…"
          disabled={isTyping}
          aria-label="Type your question about the policy"
          autoComplete="off"
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage}
          disabled={!canSend}
          aria-label="Send message"
        >
          Send
        </button>
      </div>

      {/* Disclaimer */}
      <p className="chat-disclaimer">
        This assistant explains policy coverage, not medical advice.
      </p>
    </div>
  );
};

export default ChatPanel;
