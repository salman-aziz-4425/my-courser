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

export default function CodeViewer({ file, onSave }) {
  const [editing, setEditing] = useState(false)
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)
  const textareaRef = useRef(null)

  useEffect(() => {
    setEditing(false)
    setContent(file?.content || '')
    setDirty(false)
  }, [file?.path])

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
