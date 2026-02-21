import { useState, useRef, useEffect } from 'react'

export default function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let aiText = ''

      setMessages((prev) => [...prev, { role: 'ai', text: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.text) {
              aiText += parsed.text
              setMessages((prev) => {
                const updated = [...prev]
                updated[updated.length - 1] = { role: 'ai', text: aiText }
                return updated
              })
            }
          } catch {}
        }
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'ai', text: `Error: ${err.message}` }])
    }

    setLoading(false)
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  function renderText(text) {
    const parts = text.split(/(```[\s\S]*?```)/g)
    return parts.map((part, i) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3)
        const firstNewline = code.indexOf('\n')
        const content = firstNewline > -1 ? code.slice(firstNewline + 1) : code
        return <pre key={i}><code>{content}</code></pre>
      }
      const lines = part.split('\n')
      return lines.map((line, j) => {
        if (!line) return null
        const boldParsed = line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        const codeParsed = boldParsed.replace(/`([^`]+)`/g, '<code>$1</code>')
        return <p key={`${i}-${j}`} dangerouslySetInnerHTML={{ __html: codeParsed }} />
      })
    })
  }

  return (
    <>
      <div className="chat-area">
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-dim)', fontSize: 13, padding: 8 }}>
            Ask anything about your codebase.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.role === 'ai' ? renderText(msg.text) : msg.text}
          </div>
        ))}
        {loading && (
          <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>
            <span className="spinner" /> Thinking...
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about your code..."
          rows={2}
          disabled={loading}
        />
        <button className="btn btn-primary btn-send" onClick={send} disabled={loading}>
          Send
        </button>
      </div>
    </>
  )
}
