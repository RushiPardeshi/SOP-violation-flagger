import re
from typing import List


def chunk_sop_document(content: str, title: str, chunk_size: int = 800, overlap: int = 100) -> List[dict]:
    """
    Intelligently chunk SOP documents for better retrieval.
    
    Strategy:
    1. Split on numbered sections (e.g., "1.1 Title", "2.3 Rules")
    2. If sections too large, split on paragraphs
    3. If paragraphs too large, split by character count with overlap
    
    Args:
        content: Full SOP document text
        title: Document title (for metadata)
        chunk_size: Target chunk size in characters
        overlap: Character overlap between chunks
    
    Returns:
        List of chunk dicts with text and metadata
    """
    chunks = []
    
    # Strategy 1: Try to split on numbered sections (e.g., "1.1", "2.3", "3.1.1")
    section_pattern = r'\n(\d+(?:\.\d+)*)\s+([^\n]+)\n'
    sections = re.split(section_pattern, content)
    
    if len(sections) > 1:
        # We found sections
        chunks = _chunk_by_sections(sections, title, chunk_size, overlap)
    else:
        # No clear sections, split by paragraphs
        chunks = _chunk_by_paragraphs(content, title, chunk_size, overlap)
    
    return chunks


def _chunk_by_sections(sections: List[str], title: str, chunk_size: int, overlap: int) -> List[dict]:
    """Chunk content that's already split by section markers."""
    chunks = []
    
    # sections format after re.split: [preamble, section_num, section_title, section_content, ...]
    preamble = sections[0].strip()
    if preamble and len(preamble) > 50:
        # Include preamble as first chunk if substantial
        chunks.append({
            "text": preamble,
            "metadata": {"section": "preamble", "title": title}
        })
    
    # Process section triplets
    i = 1
    while i < len(sections):
        if i + 2 < len(sections):
            section_num = sections[i]
            section_title = sections[i + 1]
            section_content = sections[i + 2].strip()
            
            section_header = f"{section_num} {section_title}".strip()
            section_full = f"{section_header}\n\n{section_content}"
            
            # If section is too large, sub-chunk it
            if len(section_full) > chunk_size * 1.5:
                sub_chunks = _chunk_by_paragraphs(section_full, title, chunk_size, overlap)
                for sub_chunk in sub_chunks:
                    sub_chunk["metadata"]["section"] = section_header
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "text": section_full,
                    "metadata": {"section": section_header, "title": title}
                })
            
            i += 3
        else:
            i += 1
    
    return chunks


def _chunk_by_paragraphs(content: str, title: str, chunk_size: int, overlap: int) -> List[dict]:
    """Chunk by paragraph boundaries with size constraints."""
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_len = len(para)
        
        # If single paragraph exceeds chunk_size, split it
        if para_len > chunk_size * 1.5:
            # Flush current chunk first
            if current_chunk:
                chunks.append({
                    "text": "\n\n".join(current_chunk),
                    "metadata": {"title": title}
                })
                current_chunk = []
                current_size = 0
            
            # Split large paragraph by sentences or character boundaries
            sub_chunks = _chunk_by_chars(para, chunk_size, overlap)
            for sub_text in sub_chunks:
                chunks.append({
                    "text": sub_text,
                    "metadata": {"title": title}
                })
        
        # Try to add paragraph to current chunk
        elif current_size + para_len + 2 <= chunk_size:  # +2 for \n\n
            current_chunk.append(para)
            current_size += para_len + 2
        
        else:
            # Flush current chunk and start new one
            if current_chunk:
                chunks.append({
                    "text": "\n\n".join(current_chunk),
                    "metadata": {"title": title}
                })
            current_chunk = [para]
            current_size = para_len
    
    # Flush remaining
    if current_chunk:
        chunks.append({
            "text": "\n\n".join(current_chunk),
            "metadata": {"title": title}
        })
    
    return chunks


def _chunk_by_chars(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Last resort: chunk by character count with overlap."""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to break at a sentence or space
        if end < text_len:
            # Look for sentence boundary
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            last_space = text.rfind(' ', start, end)
            
            break_point = max(last_period, last_newline, last_space)
            if break_point > start:
                end = break_point + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap if end < text_len else end
    
    return chunks
