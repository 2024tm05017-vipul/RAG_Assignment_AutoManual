"""Vision Language Model - Image summarization"""

import logging
from typing import Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisionLanguageModel:
    """VLM for generating image captions/summaries"""
    
    def __init__(self, model_name: str = "llava-hf/llava-1.5-7b-hf",
                 use_4bit: bool = True):
        """
        Args:
            model_name: HuggingFace model ID
            use_4bit: Use 4-bit quantization
        """
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            from PIL import Image
            import torch
        except ImportError:
            raise ImportError("Required packages not installed. Run: pip install pillow transformers torch")
        
        self.model_name = model_name
        self.torch = torch
        self.Image = Image
        
        logger.info(f"Loading Vision Language Model: {model_name}")
        
        try:
            self.processor = AutoProcessor.from_pretrained(model_name)
            
            if use_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=self.torch.float16,
                    )
                    self.model = LlavaForConditionalGeneration.from_pretrained(
                        model_name,
                        quantization_config=bnb_config,
                        device_map="auto"
                    )
                    logger.info("VLM loaded with 4-bit quantization")
                except Exception as e:
                    logger.warning(f"4-bit quantization failed: {e}. Loading without...")
                    self.model = LlavaForConditionalGeneration.from_pretrained(model_name, device_map="auto")
            else:
                self.model = LlavaForConditionalGeneration.from_pretrained(model_name, device_map="auto")
            
            logger.info("VLM loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading VLM: {e}")
            logger.warning("VLM will be disabled for image processing")
            self.model = None
            self.processor = None
    
    def summarize_image(self, image_path: str) -> str:
        """
        Generate a summary of an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Text summary of image
        """
        if self.model is None:
            return "Image processing disabled (VLM not loaded)"
        
        try:
            # Load image
            image = self.Image.open(image_path).convert("RGB")
            
            # Prompt for technical diagram analysis
            prompt = """Analyze this automotive engineering diagram or image and provide a concise technical summary.

Include:
1. Main components shown
2. Key assembly sequence or layout
3. Any performance specifications visible
4. Safety considerations

Keep summary to 80-120 words. Use technical automotive terminology."""
            
            # Process inputs
            inputs = self.processor(prompt, image, return_tensors="pt")
            
            # Generate
            with self.torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.3,
                    do_sample=False
                )
            
            # Decode
            summary = self.processor.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            
            logger.info(f"Generated image summary for {Path(image_path).name}")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing image {image_path}: {e}")
            return f"Error processing image: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if VLM is available"""
        return self.model is not None
