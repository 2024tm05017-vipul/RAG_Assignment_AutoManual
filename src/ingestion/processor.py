"""Chunk processor - Break content into chunks with metadata"""

import logging
import uuid
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Process parsed PDF content into embedable chunks"""
    
    def __init__(self, 
                 text_chunk_size: int = 300,
                 text_overlap: int = 50,
                 table_chunk_size: int = 500):
        """
        Args:
            text_chunk_size: Characters per text chunk
            text_overlap: Character overlap between chunks
            table_chunk_size: Characters per table chunk
        """
        self.text_chunk_size = text_chunk_size
        self.text_overlap = text_overlap
        self.table_chunk_size = table_chunk_size
    
    def process(self, parsed_content: Dict) -> Dict:
        """
        Process parsed PDF content into chunks.
        
        Args:
            parsed_content: Output from PDFParser.parse()
            
        Returns:
            dict with chunks organized by type
        """
        chunks = {
            "text_chunks": [],
            "table_chunks": [],
            "image_chunks": [],
            "metadata": parsed_content.get("metadata", {}),
            "filename": parsed_content.get("filename", "unknown")
        }
        
        # Process text content
        for text_block in parsed_content.get("text_content", []):
            text_chunks = self._chunk_text(
                text_block["content"],
                page=text_block["page"],
                filename=parsed_content.get("filename")
            )
            chunks["text_chunks"].extend(text_chunks)
        
        # Process tables
        for table in parsed_content.get("tables", []):
            table_chunks = self._chunk_table(
                table["content"],
                page=table["page"],
                table_index=table.get("table_index", 0),
                filename=parsed_content.get("filename")
            )
            chunks["table_chunks"].extend(table_chunks)
        
        # Process images
        for image in parsed_content.get("images", []):
            image_chunks = self._chunk_image(
                image,
                filename=parsed_content.get("filename")
            )
            chunks["image_chunks"].extend(image_chunks)
        
        return chunks
    
    def _chunk_text(self, text: str, page: int, filename: str) -> List[Dict]:
        """Break text into overlapping chunks"""
        chunks = []
        
        if not text.strip():
            return chunks
        
        # Simple sentence-aware chunking
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= self.text_chunk_size:
                chunk_text = " ".join(current_chunk)
                chunk = {
                    "id": str(uuid.uuid4()),
                    "content": chunk_text,
                    "type": "text",
                    "page": page,
                    "filename": filename,
                    "chunk_size": len(chunk_text),
                    "created_at": datetime.now().isoformat()
                }
                chunks.append(chunk)
                
                # Reset with overlap
                overlap_words = max(1, len(current_chunk) // 3)
                current_chunk = current_chunk[-overlap_words:]
                current_size = sum(len(w) for w in current_chunk) + len(current_chunk)
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = {
                "id": str(uuid.uuid4()),
                "content": chunk_text,
                "type": "text",
                "page": page,
                "filename": filename,
                "chunk_size": len(chunk_text),
                "created_at": datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_table(self, table_content: str, page: int, table_index: int, 
                     filename: str) -> List[Dict]:
        """Create chunk for table (tables typically kept whole)"""
        
        if not table_content.strip():
            return []
        
        chunk = {
            "id": str(uuid.uuid4()),
            "content": table_content,
            "type": "table",
            "page": page,
            "table_index": table_index,
            "filename": filename,
            "chunk_size": len(table_content),
            "created_at": datetime.now().isoformat()
        }
        
        return [chunk]
    
    def _chunk_image(self, image: Dict, filename: str) -> List[Dict]:
        """Create chunk for image (for later VLM processing)"""
        
        chunk = {
            "id": str(uuid.uuid4()),
            "image_path": image.get("path"),
            "image_filename": image.get("filename"),
            "type": "image",
            "page": image.get("page"),
            "image_index": image.get("image_index", 0),
            "source_filename": filename,
            "created_at": datetime.now().isoformat(),
            "summary": None  # Will be filled by VLM
        }
        
        return [chunk]
