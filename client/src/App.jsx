import { useState, useEffect } from 'react'
import FileTree from './components/FileTree'
import CodeViewer from './components/CodeViewer'
import ChatPanel from './components/ChatPanel'
import SearchPanel from './components/SearchPanel'

export default function App() {
  const [tree, setTree] = useState([])
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState(null)
  const [tab, setTab] = useState('chat')
  const [indexing, setIndexing] = useState(false)
  const [toast, setToast] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [panelOpen, setPanelOpen] = useState(true)

  useEffect(() => {
    loadTree()
    loadStatus()
  }, [])

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 3000)
    return () => clearTimeout(t)
  }, [toast])

  async function loadTree() {
    try {
      const res = await fetch('/api/tree')
      setTree(await res.json())
    } catch {}
  }

  async function loadStatus() {
    try {
      const res = await fetch('/api/status')
      setStatus(await res.json())
    } catch {}
  }

  async function openFile(path) {
    try {
      const res = await fetch(`/api/file?path=${encodeURIComponent(path)}`)
      const data = await res.json()
      if (!data.error) setFile(data)
    } catch {}
  }

  async function runIndex() {
    setIndexing(true)
    setToast({ type: 'info', text: 'Indexing project...' })
    try {
      const res = await fetch('/api/index', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      const data = await res.json()
      setToast({ type: 'success', text: data.message })
      loadStatus()
    } catch (err) {
      setToast({ type: 'error', text: 'Index failed' })
    }
    setIndexing(false)
  }

  const chunks = status?.index?.chunks_count ?? 0

  return (
    <>
      {/* Header */}
      <header className="header">
        <span className="logo">&#9670; mycoursor</span>
        <span className="file-name">{file ? file.path.split('/').pop() : 'No file open'}</span>
        <div className="actions">
          <button className="btn" onClick={runIndex} disabled={indexing}>
            {indexing ? 'Indexing...' : 'Index'}
          </button>
          <span className={`dot ${chunks > 0 ? 'green' : 'yellow'}`} title={`${chunks} chunks`} />
        </div>
      </header>

      {/* Main layout */}
      <div className="layout">
        {/* Sidebar - file explorer */}
        <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
          <div className="sidebar-header">
            <span className="sidebar-title">Explorer</span>
            <button className="collapse-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? '◂' : '▸'}
            </button>
          </div>
          {sidebarOpen && <FileTree tree={tree} onSelect={openFile} activePath={file?.path} />}
        </aside>

        {/* Center - code viewer */}
        <main className="editor-area">
          {file ? (
            <CodeViewer file={file} />
          ) : (
            <div className="welcome">
              <h1>&#9670; mycoursor</h1>
              <p>AI-powered code assistant</p>
              <div className="welcome-btns">
                <button className="btn btn-primary" onClick={runIndex} disabled={indexing}>
                  {indexing ? 'Indexing...' : 'Index Project'}
                </button>
              </div>
              {status && (
                <div className="status-box">
                  <div>LLM: {status.llm_model}</div>
                  <div>Database: {status.database}</div>
                  <div>Indexed chunks: {chunks}</div>
                </div>
              )}
            </div>
          )}
        </main>

        {/* Right panel - chat / search */}
        <aside className={`panel ${panelOpen ? '' : 'collapsed'}`}>
          <div className="panel-header">
            <button className="collapse-btn" onClick={() => setPanelOpen(!panelOpen)}>
              {panelOpen ? '▸' : '◂'}
            </button>
            {panelOpen && (
              <div className="panel-tabs">
                <button className={`panel-tab ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
                  AI Chat
                </button>
                <button className={`panel-tab ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>
                  Search
                </button>
              </div>
            )}
          </div>

          {panelOpen && tab === 'chat' && <ChatPanel />}
          {panelOpen && tab === 'search' && <SearchPanel onFileSelect={openFile} />}
        </aside>
      </div>

      {/* Toast */}
      {toast && (
        <div className="toast-container">
          <div className={`toast ${toast.type}`}>{toast.text}</div>
        </div>
      )}
    </>
  )
}
