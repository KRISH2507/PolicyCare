from typing import List, Dict

SECTION_HEADERS = [
    "OVERVIEW", "PREMIUM", "ELIGIBILITY", "INCLUSIONS", "EXCLUSIONS",
    "WAITING PERIODS", "SUB-LIMITS", "CO-PAY", "CLAIM TYPE",
    "SUITABILITY", "NETWORK HOSPITALS",
]


def _is_section_header(line: str) -> str | None:
    stripped = line.strip().upper()
    for header in SECTION_HEADERS:
        if stripped in (header, header + ":"):
            return header
    return None


def chunk_by_section(text: str, policy_name: str, insurer: str) -> List[Dict]:
    lines = text.splitlines()
    sections: List[tuple[str, List[str]]] = []
    current_section = "HEADER"
    current_lines: List[str] = []

    for line in lines:
        header = _is_section_header(line)
        if header:
            if current_lines:
                sections.append((current_section, current_lines))
            current_section = header
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_section, current_lines))

    chunks = []
    for idx, (section_name, section_lines) in enumerate(sections):
        body = "\n".join(l for l in section_lines if l.strip())
        if not body.strip():
            continue
        chunks.append({
            "text": f"Policy: {policy_name}\nInsurer: {insurer}\nSection: {section_name}\n\n{body}",
            "policy_name": policy_name,
            "insurer": insurer,
            "section": section_name,
            "chunk_index": idx,
            "page_number": 1,
        })

    return chunks


def chunk_document(pages: List[Dict], chunk_size: int = 300, overlap: int = 50) -> List[Dict]:
    chunks = []
    for page in pages:
        text = page.get("text", "")
        page_num = page.get("page", 1)
        words = text.split()
        if not words:
            continue
        chunk_index = 0
        i = 0
        while i < len(words):
            chunk_text = " ".join(words[i: i + chunk_size]).strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page_number": page_num, "chunk_index": chunk_index})
            chunk_index += 1
            i += chunk_size - overlap
    return chunks
