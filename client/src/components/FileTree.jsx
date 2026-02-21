import { useState } from 'react'

function FileNode({ node, onSelect, activePath, depth = 0 }) {
  const [open, setOpen] = useState(depth < 1)

  if (node.type === 'dir') {
    return (
      <div>
        <div
          className="tree-item"
          style={{ paddingLeft: 8 + depth * 12 }}
          onClick={() => setOpen(!open)}
        >
          <span className="tree-icon">{open ? '▾' : '▸'}</span>
          {node.name}
        </div>
        {open && (
          <div className="tree-children">
            {node.children.map((child) => (
              <FileNode
                key={child.path}
                node={child}
                onSelect={onSelect}
                activePath={activePath}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      className={`tree-item ${activePath === node.path ? 'active' : ''}`}
      style={{ paddingLeft: 8 + depth * 12 }}
      onClick={() => onSelect(node.path)}
    >
      <span className="tree-icon">📄</span>
      {node.name}
    </div>
  )
}

export default function FileTree({ tree, onSelect, activePath }) {
  if (!tree || tree.length === 0) {
    return <div style={{ padding: 12, color: 'var(--text-dim)', fontSize: 12 }}>No files found</div>
  }

  return (
    <div className="file-tree">
      {tree.map((node) => (
        <FileNode key={node.path} node={node} onSelect={onSelect} activePath={activePath} />
      ))}
    </div>
  )
}
