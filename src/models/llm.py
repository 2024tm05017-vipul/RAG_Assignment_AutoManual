"""LLM wrapper - Local inference with quantization for 8GB RAM"""

import logging
import torch
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMWrapper:
    """Wrapper for local LLM with quantization support"""
    
    def __init__(self, model_name: str = "microsoft/phi-2", 
                 use_4bit: bool = True,
                 max_tokens: int = 512,
                 temperature: float = 0.3):
        """
        Args:
            model_name: HuggingFace model ID
            use_4bit: Use 4-bit quantization
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        except ImportError:
            raise ImportError("transformers not installed. Run: pip install transformers")
        
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.device = "cpu"
        
        logger.info(f"Loading LLM: {model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model with quantization if specified
        if use_4bit:
            try:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=bnb_config,
                    device_map="auto"
                )
                logger.info("LLM loaded with 4-bit quantization")
            except Exception as e:
                logger.warning(f"4-bit quantization failed: {e}. Loading without quantization...")
                self.model = AutoModelForCausalLM.from_pretrained(model_name)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
        
        self.model.eval()
        logger.info(f"LLM loaded successfully")
    
    def generate(self, prompt: str, max_length: Optional[int] = None) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_length: Maximum length (uses self.max_tokens if not specified)
            
        Returns:
            Generated text
        """
        max_length = max_length or self.max_tokens
        
        try:
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Inference
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=self.temperature,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from output
            if prompt in generated_text:
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def __call__(self, prompt: str) -> str:
        """Call the generator directly"""
        return self.generate(prompt)
