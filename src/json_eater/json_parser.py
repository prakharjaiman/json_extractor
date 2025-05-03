from __future__ import annotations
import json, textwrap
from typing import Dict, List, Any

Pointer = str
MAX_ENUM = 10

def _resolve_pointer(root: Dict[str, Any], ptr: Pointer) -> Dict[str, Any]:
    """Internal $ref resolver (only handles pointers within the same document)."""
    if not ptr.startswith("#/"):
        raise ValueError(f"External reference not supported: {ptr!r}")
    node: Any = root
    for token in ptr[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[token]
    if not isinstance(node, dict):
        raise TypeError(f"$ref did not resolve to an object: {ptr}")
    return node

def extract_structure(
    schema: Dict[str, Any],
    *,
    root_name: str | None = None,
    show_patterns: bool = True,
) -> str:
    """
    Return an indented outline of a JSON‑Schema, covering $ref, anyOf/oneOf/allOf, etc.
    """

    def _headline(node: Dict[str, Any], name: str) -> str:
        parts: List[str] = []
        if "description" in node:
            parts.append(node["description"])

        if "type" in node:
            parts.append(f"type={node['type']}")

        if "enum" in node:
            enum_vals = node["enum"]
            if len(enum_vals) > MAX_ENUM:
                enum_display = f"{enum_vals[:MAX_ENUM]}…(+{len(enum_vals)-MAX_ENUM} more)"
            else:
                enum_display = str(enum_vals)
            parts.append(f"enum={enum_display}")

        if "format" in node:
            parts.append(f"format={node['format']}")

        if show_patterns and "pattern" in node:
            pat = node["pattern"]
            if len(pat) > 40:
                pat = pat[:37] + "…"
            parts.append(f"pattern=/{pat}/")

        if "default" in node:
            parts.append(f"default={node['default']}")

        if "examples" in node:
            parts.append(f"examples={node['examples'][:3]}{'…' if len(node['examples'])>3 else ''}")

        return "; ".join(parts)

    # ------------------------------------------------------------------
    def _walk(node: Dict[str, Any],
              name: str,
              indent: int,
              out: List[str],
              required: List[str] | None = None) -> None:
        # ---- resolve $ref -------------------------------------------------
        while "$ref" in node:
            node = _resolve_pointer(schema, node["$ref"]) | node
            node.pop("$ref", None)

        # ---- emit this node ----------------------------------------------
        bullet = "- " if indent else ""
        req_flag = " (required)" if required and name in required else ""
        out.append(f"{'    '*indent}{bullet}{name}: {_headline(node, name)}{req_flag}")

        # ---- recurse based on structural keywords ------------------------
        ntype = node.get("type")

        # objects ----------------------------------------------------------
        if ntype == "object":
            child_required = node.get("required", [])
            if node.get("additionalProperties") is False:
                out.append(f"{'    '*(indent+1)}⤷ additional=false")
            for prop, sub in node.get("properties", {}).items():
                _walk(sub, prop, indent + 1, out, child_required)

        # arrays -----------------------------------------------------------
        elif ntype == "array" and "items" in node:
            if node.get("additionalItems") is False:
                out.append(f"{'    '*(indent+1)}⤷ additional=false")
            _walk(node["items"], "[items]", indent + 1, out)

        # combinators ------------------------------------------------------
        for kw in ("anyOf", "oneOf", "allOf"):
            if kw in node:
                for i, variant in enumerate(node[kw]):
                    _walk(variant, f"{kw}[{i}]", indent + 1, out)

    # ------------------------------------------------------------------
    lines: List[str] = []
    root_label = root_name or schema.get("title", "")
    _walk(schema, root_label, 0, lines)
    return "\n".join(lines)

# ----------------------------------------------------------------------
# quick demo: comment out in production
if __name__ == "__main__":
    with open("/Users/prakhar/Desktop/playground/json_extractor/keys/convert your resume to this schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
    print((extract_structure(schema, root_name="CFF")))
