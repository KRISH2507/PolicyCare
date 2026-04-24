from typing import List, Dict

def chunk_document(pages: List[Dict], chunk_size: int = 300, overlap: int = 50) -> List[Dict]:
    """
    Slices raw token list strings (pages) into manageable sliding vectors
    with overlapping contexts ensuring sentences don't rigidly cut off data context.
    """
    
    chunks = []
    
    for page in pages:
        text = page.get("text", "")
        page_num = page.get("page", 1)
        
        words = text.split()
        chunk_index = 0
        i = 0
        
        if not words:
            continue
            
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words).strip()
            
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page_number": page_num,
                    "chunk_index": chunk_index
                })
                
            chunk_index += 1
            i += (chunk_size - overlap)
            
    return chunks