import { useState, useEffect, useRef } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

const LANG_MAP = {
  python: 'python',
  javascript: 'javascript',
  typescript: 'typescript',
  rust: 'rust',
  go: 'go',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
  ruby: 'ruby',
  php: 'php',
  bash: 'bash',
  html: 'html',
  css: 'css',
  json: 'json',
  yaml: 'yaml',
  toml: 'toml',
  markdown: 'markdown',
  sql: 'sql',
}

export default function CodeViewer({ file, pendingEdit, onAnimationDone, onSave }) {
  const [editing, setEditing] = useState(false)
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [animState, setAnimState] = useState(null)
  const textareaRef = useRef(null)
  const animTimerRef = useRef(null)
  const fadeTimerRef = useRef(null)
  const codeContentRef = useRef(null)

  useEffect(() => {
    setEditing(false)
    setContent(file?.content || '')
    setDirty(false)
  }, [file?.path])

  useEffect(() => {
    if (animTimerRef.current) clearInterval(animTimerRef.current)
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current)

    if (!pendingEdit || !file) return

    const updatedText = pendingEdit.updated.trimEnd()
    const originalText = pendingEdit.original.trimEnd()

    if (!updatedText) {
      if (onAnimationDone) onAnimationDone()
      return
    }

    const fileContent = file.content
    let idx = -1

    if (originalText) {
      const origIdx = fileContent.indexOf(updatedText)
      if (origIdx !== -1) {
        idx = origIdx
      }
    }

    if (idx === -1) {
      idx = fileContent.indexOf(updatedText)
    }

    if (idx === -1) {
      if (onAnimationDone) onAnimationDone()
      return
    }

    const beforeText = fileContent.substring(0, idx)
    const startLine = beforeText.split('\n').length
    const updatedLines = updatedText.split('\n')
    const endLine = startLine + updatedLines.length - 1

    setAnimState({
      startLine,
      endLine,
      text: updatedText,
      revealedChars: 0,
      totalChars: updatedText.length,
      done: false,
    })

    let chars = 0
    const speed = Math.max(5, Math.min(20, 1500 / updatedText.length))

    animTimerRef.current = setInterval(() => {
      chars += 3
      if (chars >= updatedText.length) {
        chars = updatedText.length
        clearInterval(animTimerRef.current)
        animTimerRef.current = null
        setAnimState(prev => prev ? { ...prev, revealedChars: chars, done: true } : null)
        fadeTimerRef.current = setTimeout(() => {
          fadeTimerRef.current = null
          setAnimState(null)
          if (onAnimationDone) onAnimationDone()
        }, 800)
        return
      }
      setAnimState(prev => prev ? { ...prev, revealedChars: chars } : null)
    }, speed)

    return () => {
      if (animTimerRef.current) { clearInterval(animTimerRef.current); animTimerRef.current = null }
      if (fadeTimerRef.current) { clearTimeout(fadeTimerRef.current); fadeTimerRef.current = null }
    }
  }, [pendingEdit])

  useEffect(() => {
    if (!animState || !codeContentRef.current) return
    const highlightEl = codeContentRef.current.querySelector('.typewriter-block')
    if (highlightEl) {
      highlightEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [animState?.startLine])

  if (!file) {
    return (
      <div className="welcome">
        <h1>mycoursor</h1>
        <p>Select a file from the explorer or use AI Chat</p>
      </div>
    )
  }

  const lang = LANG_MAP[file.lang] || 'text'

  function startEditing() {
    setContent(file.content)
    setEditing(true)
    setDirty(false)
    setTimeout(() => textareaRef.current?.focus(), 0)
  }

  function cancelEditing() {
    setEditing(false)
    setContent(file.content)
    setDirty(false)
  }

  async function handleSave() {
    setSaving(true)
    try {
      const res = await fetch('/api/file', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: file.path, content }),
      })
      if (res.ok) {
        const data = await res.json()
        if (onSave) onSave(data)
        setEditing(false)
        setDirty(false)
      }
    } catch (err) {
      console.error('Save failed', err)
    }
    setSaving(false)
  }

  function handleKeyDown(e) {
    if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      handleSave()
    }
    if (e.key === 'Escape') {
      cancelEditing()
    }
    if (e.key === 'Tab') {
      e.preventDefault()
      const ta = textareaRef.current
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const val = content
      setContent(val.substring(0, start) + '  ' + val.substring(end))
      setDirty(true)
      setTimeout(() => { ta.selectionStart = ta.selectionEnd = start + 2 }, 0)
    }
  }

  function renderAnimatedContent() {
    if (!animState) return null

    const lines = file.content.split('\n')
    const { startLine, endLine, text, revealedChars, done } = animState

    const beforeLines = lines.slice(0, startLine - 1)
    const afterLines = lines.slice(endLine)
    const revealedText = text.substring(0, revealedChars)
    const hiddenText = text.substring(revealedChars)

    return (
      <div className="code-content typewriter-active" ref={codeContentRef}>
        {beforeLines.length > 0 && (
          <SyntaxHighlighter
            language={lang}
            style={oneDark}
            showLineNumbers
            startingLineNumber={1}
            customStyle={{ margin: 0, background: 'transparent', fontSize: 13 }}
          >
            {beforeLines.join('\n')}
          </SyntaxHighlighter>
        )}

        <div className={`typewriter-block ${done ? 'typewriter-done' : ''}`}>
          <div className="typewriter-line-numbers">
            {text.split('\n').map((_, i) => (
              <div key={i} className="typewriter-ln">{startLine + i}</div>
            ))}
          </div>
          <div className="typewriter-code">
            <span className="typewriter-revealed">{revealedText}</span>
            {!done && <span className="typewriter-cursor">█</span>}
            <span className="typewriter-hidden">{hiddenText}</span>
          </div>
        </div>

        {afterLines.length > 0 && (
          <SyntaxHighlighter
            language={lang}
            style={oneDark}
            showLineNumbers
            startingLineNumber={endLine + 1}
            customStyle={{ margin: 0, background: 'transparent', fontSize: 13 }}
          >
            {afterLines.join('\n')}
          </SyntaxHighlighter>
        )}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="code-header">
        <span>{file.path}{dirty ? ' *' : ''}</span>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span>{lang}</span>
          {editing ? (
            <>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ padding: '3px 10px', fontSize: 11 }}>
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button className="btn" onClick={cancelEditing} style={{ padding: '3px 10px', fontSize: 11 }}>
                Cancel
              </button>
            </>
          ) : (
            <button className="btn" onClick={startEditing} style={{ padding: '3px 10px', fontSize: 11 }}>
              Edit
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="code-content">
          <textarea
            ref={textareaRef}
            className="code-editor"
            value={content}
            onChange={(e) => { setContent(e.target.value); setDirty(true) }}
            onKeyDown={handleKeyDown}
            spellCheck={false}
          />
        </div>
      ) : animState ? (
        renderAnimatedContent()
      ) : (
        <div className="code-content">
          <SyntaxHighlighter
            language={lang}
            style={oneDark}
            showLineNumbers
            customStyle={{ margin: 0, background: 'transparent', fontSize: 13 }}
          >
            {file.content}
          </SyntaxHighlighter>
        </div>
      )}
    </div>
  )
}
