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

export default function CodeViewer({ file }) {
  if (!file) {
    return (
      <div className="welcome">
        <h1>mycoursor</h1>
        <p>Select a file from the explorer or use AI Chat</p>
      </div>
    )
  }

  const lang = LANG_MAP[file.lang] || 'text'
  const fileName = file.path.split('/').pop()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="code-header">
        <span>{file.path}</span>
        <span>{lang}</span>
      </div>
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
    </div>
  )
}
