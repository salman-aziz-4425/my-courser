import { useState, useRef, useEffect } from 'react'

const EDIT_REGEX = /```edit\s*\nFILE:\s*(.+?)\s*\n<<<<<<< ORIGINAL\s*\n([\s\S]*?)=======\s*\n([\s\S]*?)>>>>>>> UPDATED\s*\n```/g

function parseEdits(text) {
  const edits = []
  let match
  const regex = new RegExp(EDIT_REGEX.source, 'g')
  while ((match = regex.exec(text)) !== null) {
    edits.push({
      full: match[0],
      file: match[1].trim(),
      original: match[2],
      updated: match[3],
    })
  }
  return edits
}

export default function ChatPanel({ currentFile, onFileUpdated }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [appliedEdits, setAppliedEdits] = useState({})
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
        body: JSON.stringify({ question, file_path: currentFile?.path || '' }),
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

  async function applyEdit(edit, editKey) {
    setAppliedEdits((prev) => ({ ...prev, [editKey]: 'applying' }))
    try {
      const res = await fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: edit.file,
          original: edit.original,
          updated: edit.updated,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setAppliedEdits((prev) => ({ ...prev, [editKey]: 'applied' }))
        if (onFileUpdated) onFileUpdated(data, { original: edit.original, updated: edit.updated })
      } else {
        const err = await res.json()
        setAppliedEdits((prev) => ({ ...prev, [editKey]: 'error' }))
        console.error('Apply failed:', err.detail)
      }
    } catch (err) {
      setAppliedEdits((prev) => ({ ...prev, [editKey]: 'error' }))
      console.error('Apply failed:', err)
    }
  }

  function renderEditBlock(edit, editKey) {
    const status = appliedEdits[editKey]
    const fileName = edit.file.split('/').pop()
    return (
      <div key={editKey} className="edit-block">
        <div className="edit-block-header">
          <span className="edit-block-file">{fileName}</span>
          {status === 'applied' ? (
            <span className="edit-block-applied">Applied</span>
          ) : status === 'applying' ? (
            <span className="edit-block-applying"><span className="spinner" /> Applying...</span>
          ) : status === 'error' ? (
            <button className="btn edit-block-btn" onClick={() => applyEdit(edit, editKey)}>Retry</button>
          ) : (
            <button className="btn btn-primary edit-block-btn" onClick={() => applyEdit(edit, editKey)}>Apply</button>
          )}
        </div>
        <div className="edit-block-diff">
          {edit.original.trim() && (
            <div className="diff-section diff-remove">
              {edit.original.split('\n').filter(l => l.trim()).slice(0, 8).map((line, i) => (
                <div key={i}>- {line}</div>
              ))}
              {edit.original.split('\n').filter(l => l.trim()).length > 8 && <div>...</div>}
            </div>
          )}
          <div className="diff-section diff-add">
            {edit.updated.split('\n').filter(l => l.trim()).slice(0, 8).map((line, i) => (
              <div key={i}>+ {line}</div>
            ))}
            {edit.updated.split('\n').filter(l => l.trim()).length > 8 && <div>...</div>}
          </div>
        </div>
      </div>
    )
  }

  function renderText(text, msgIndex) {
    const edits = parseEdits(text)

    if (edits.length === 0) {
      return renderPlainText(text)
    }

    const parts = []
    let remaining = text
    edits.forEach((edit, editIdx) => {
      const idx = remaining.indexOf(edit.full)
      if (idx > 0) {
        parts.push({ type: 'text', content: remaining.substring(0, idx) })
      }
      parts.push({ type: 'edit', edit, key: `${msgIndex}-${editIdx}` })
      remaining = remaining.substring(idx + edit.full.length)
    })
    if (remaining.trim()) {
      parts.push({ type: 'text', content: remaining })
    }

    return parts.map((part, i) => {
      if (part.type === 'edit') {
        return renderEditBlock(part.edit, part.key)
      }
      return <span key={i}>{renderPlainText(part.content)}</span>
    })
  }

  function renderPlainText(text) {
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
            {currentFile && (
              <div style={{ marginTop: 6, fontSize: 11 }}>
                Editing: <span style={{ color: 'var(--accent)' }}>{currentFile.path.split('/').pop()}</span>
              </div>
            )}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.role === 'ai' ? renderText(msg.text, i) : msg.text}
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
          placeholder={currentFile ? `Ask about ${currentFile.path.split('/').pop()}...` : 'Ask about your code...'}
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
