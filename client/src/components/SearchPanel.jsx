import { useState } from 'react'

export default function SearchPanel({ onFileSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  async function doSearch() {
    const q = query.trim()
    if (!q) return
    setLoading(true)
    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setResults([])
    }
    setLoading(false)
  }

  function handleKey(e) {
    if (e.key === 'Enter') doSearch()
  }

  return (
    <>
      <div className="input-row" style={{ borderTop: 'none', borderBottom: '1px solid var(--border)' }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Semantic search..."
        />
        <button className="btn btn-primary btn-send" onClick={doSearch} disabled={loading}>
          {loading ? '...' : 'Go'}
        </button>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {results.map((r, i) => {
          const shortPath = r.file_path.split('/').slice(-2).join('/')
          return (
            <div
              key={i}
              className="search-result"
              onClick={() => onFileSelect(r.file_path)}
            >
              <span className="sr-file">{shortPath}</span>
              <span className="sr-lines">:{r.start_line}-{r.end_line}</span>
              <span className="sr-score">{r.score}</span>
              <div className="sr-preview">{r.text.slice(0, 120)}</div>
            </div>
          )
        })}
        {results.length === 0 && !loading && (
          <div style={{ padding: 12, color: 'var(--text-dim)', fontSize: 12 }}>
            Search your indexed codebase.
          </div>
        )}
      </div>
    </>
  )
}
