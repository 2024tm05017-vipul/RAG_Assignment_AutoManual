"""PDF Parser - Extract text, tables, and images using PyMuPDF"""

import io
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import fitz  # PyMuPDF
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF and extract text, tables, images"""
    
    def __init__(self, dpi: int = 150):
        """
        Args:
            dpi: Resolution for image extraction
        """
        self.dpi = dpi
        
    def parse(self, pdf_path: str) -> Dict:
        """
        Parse PDF and extract all content.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict with text, tables, images, and metadata
        """
        try:
            doc = fitz.open(pdf_path)
            result = {
                "filename": Path(pdf_path).name,
                "text_content": [],
                "tables": [],
                "images": [],
                "metadata": {}
            }
            
            # Extract metadata
            result["metadata"] = {
                "total_pages": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
            }
            
            # Process each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Extract text
                text_content = self._extract_text(page, page_num)
                if text_content:
                    result["text_content"].extend(text_content)
                
                # Extract tables
                tables = self._extract_tables(page, page_num)
                if tables:
                    result["tables"].extend(tables)
                
                # Extract images
                images = self._extract_images(page, page_num, pdf_path)
                if images:
                    result["images"].extend(images)
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            raise
    
    def _extract_text(self, page, page_num: int) -> List[Dict]:
        """Extract text blocks from page"""
        text_blocks = []
        
        # Get text with layout
        text = page.get_text()
        
        if text.strip():
            text_blocks.append({
                "page": page_num + 1,
                "content": text.strip(),
                "type": "text"
            })
        
        return text_blocks
    
    def _extract_tables(self, page, page_num: int) -> List[Dict]:
        """Extract tables from page using pymupdf-table"""
        tables = []
        
        try:
            # Try to find tables
            table_list = page.find_tables()
            
            if table_list:
                for idx, table in enumerate(table_list):
                    # Convert table to list of lists
                    rows = table.extract()
                    
                    # Convert to markdown-style table
                    table_markdown = self._rows_to_markdown(rows)
                    
                    tables.append({
                        "page": page_num + 1,
                        "table_index": idx,
                        "content": table_markdown,
                        "rows": len(rows),
                        "cols": len(rows[0]) if rows else 0,
                        "type": "table"
                    })
        except Exception as e:
            logger.debug(f"No tables found on page {page_num + 1}: {e}")
        
        return tables
    
    def _extract_images(self, page, page_num: int, pdf_path: str) -> List[Dict]:
        """Extract images from page"""
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img_id in enumerate(image_list):
                try:
                    # Get image from PDF
                    xref = img_id
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Save image
                    img_filename = f"{Path(pdf_path).stem}_p{page_num + 1}_img{img_index}.png"
                    img_path = Path("/tmp") / img_filename
                    
                    if pix.n - pix.alpha < 4:  # Gray or RGB
                        pix.save(str(img_path))
                    else:  # CMYK
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                        pix.save(str(img_path))
                    
                    images.append({
                        "page": page_num + 1,
                        "image_index": img_index,
                        "path": str(img_path),
                        "filename": img_filename,
                        "type": "image"
                    })
                    
                    pix = None
                    
                except Exception as e:
                    logger.debug(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error processing images on page {page_num + 1}: {e}")
        
        return images
    
    @staticmethod
    def _rows_to_markdown(rows: List[List[str]]) -> str:
        """Convert table rows to markdown format"""
        if not rows:
            return ""
        
        # Header row
        markdown = "| " + " | ".join(str(cell).strip() for cell in rows[0]) + " |\n"
        markdown += "|" + "|".join(["---" for _ in rows[0]]) + "|\n"
        
        # Data rows
        for row in rows[1:]:
            markdown += "| " + " | ".join(str(cell).strip() for cell in row) + " |\n"
        
        return markdown
