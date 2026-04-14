import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import ReactMarkdown from 'react-markdown'

const quickQuestions = [
  'What is the current bottleneck?',
  'Show me the LOB metrics summary',
  'What is the current ALOS?',
  'Which stage has highest WIP?',
  'What corrective actions do you recommend?',
]

export default function AgentChat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    if (!text.trim()) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const res = await api.chat(text)
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Failed to get response.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ height: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="card-badge" style={{ background: 'var(--success)' }} />
            <span className="card-title">Agent Chat</span>
          </div>
          <div className="card-subtitle">Ask questions about hospital operations, metrics, and recommendations</div>
        </div>
      </div>

      <div className="card-body" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: 12 }}>
        {/* Quick questions */}
        <div className="quick-questions">
          {quickQuestions.map((q, i) => (
            <button key={i} className="quick-btn" onClick={() => sendMessage(q)} disabled={loading}>
              {q}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto' }}>
          {messages.length === 0 && (
            <div className="empty" style={{ paddingTop: 60 }}>
              Ask a question about hospital LOB metrics, bottlenecks, or recommendations.
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : msg.content}
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant">
              <div className="spinner" style={{ width: 16, height: 16, borderWidth: 1.5, margin: '0 auto' }} />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-row">
          <input
            className="chat-input"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && sendMessage(input)}
            placeholder="Ask about bottlenecks, metrics, recommendations..."
            disabled={loading}
          />
          <button className="chat-send" onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
