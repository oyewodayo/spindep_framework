import React, { useState } from "react";
import { T } from "../../constants";
import { Icon } from "./Icon";
import type { FileTreeNode } from "../../types";

interface FileTreeProps {
  node: FileTreeNode;
  depth?: number;
  onSelect?: (node: FileTreeNode) => void;
  selected?: string;
}

export const FileTree: React.FC<FileTreeProps> = ({
  node,
  depth = 0,
  onSelect,
  selected,
}) => {
  const [open, setOpen] = useState(depth < 2);
  const isFolder    = node.type === "folder";
  const isSelected  = selected === node.name;

  const handleClick = () => {
    if (isFolder) setOpen(o => !o);
    else onSelect?.(node);
  };

  return (
    <div style={{ paddingLeft: depth * 14 }}>
      <div
        className={`ftree-item${isSelected ? " selected" : ""}`}
        onClick={handleClick}
      >
        <span style={{ color: isFolder ? T.amber : T.blue, flexShrink: 0 }}>
          <Icon name={isFolder ? "folder" : "file"} size={13} />
        </span>
        <span
          style={{
            color: isFolder ? T.amber : T.text,
            fontSize: 11.5,
            fontFamily: isFolder ? T.sans : T.mono,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {node.name}
        </span>
        {!isFolder && node.rows != null && (
          <span style={{ marginLeft: "auto", fontSize: 10, color: T.muted, fontFamily: T.mono }}>
            {node.rows}r
          </span>
        )}
        {isFolder && (
          <span style={{ marginLeft: "auto", color: T.muted }}>
            <Icon name={open ? "chevD" : "chevron"} size={11} />
          </span>
        )}
      </div>

      {isFolder && open && node.children?.map((child, i) => (
        <FileTree
          key={i}
          node={child}
          depth={depth + 1}
          onSelect={onSelect}
          selected={selected}
        />
      ))}
    </div>
  );
};