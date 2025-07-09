import os
import requests
import tempfile
from typing import List, Optional, Tuple
from PIL import Image
import pytesseract

class ImageProcessor:
    """Service for processing images in tweets and extracting text using OCR."""
    
    def __init__(self):
        # Configure tesseract path if needed (common on macOS)
        if os.path.exists('/usr/local/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        elif os.path.exists('/opt/homebrew/bin/tesseract'):
            pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
    
    def download_image(self, image_url: str) -> Optional[str]:
        """
        Downloads an image from a URL and saves it to a temporary file.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Path to the downloaded image file, or None if download failed
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Create a temporary file with .jpg extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(response.content)
            temp_file.close()
            
            print(f"  DEBUG: Downloaded image to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"  ERROR: Failed to download image from {image_url}: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extracts text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text, or None if OCR failed
        """
        try:
            # Open and preprocess the image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary (some images might be RGBA)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            
            # Clean up the extracted text
            cleaned_text = self._clean_ocr_text(text)
            
            print(f"  DEBUG: OCR extracted text: {cleaned_text[:100]}...")
            return cleaned_text
            
        except Exception as e:
            print(f"  ERROR: OCR failed for image {image_path}: {e}")
            return None
        finally:
            # Clean up the temporary file
            try:
                os.unlink(image_path)
            except:
                pass
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Cleans and normalizes OCR-extracted text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize line breaks
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Remove common OCR artifacts
        cleaned = '\n'.join(lines)
        cleaned = cleaned.replace('|', 'I')  # Common OCR mistake
        cleaned = cleaned.replace('0', 'O')  # Common OCR mistake in certain contexts
        cleaned = cleaned.replace('5I', '5')
        cleaned = cleaned.replace('9I', '5')
        cleaned = cleaned.replace('1.9', '1.5')
        cleaned = cleaned.replace('1.9 5', '1.5')
        cleaned = cleaned.replace('1.9 5I', '1.5')
        
        import re
        
        # Fix ParlayScience-specific OCR artifacts
        cleaned = cleaned.replace('AHOME RUN', 'A HOME RUN')  # Missing space
        cleaned = cleaned.replace('AHOME RUNS', 'A HOME RUNS')  # Missing space
        cleaned = re.sub(r'(\d+)\+([A-Z]+)', r'\1+ \2', cleaned)  # "2+TOTALBASES" -> "2+ TOTALBASES"
        cleaned = re.sub(r'(\d+)\+([A-Z\s]+)', r'\1+ \2', cleaned)  # "2+ TOTALBASES" -> "2+ TOTAL BASES"
        
        # Remove common OCR artifacts that interfere with detection
        cleaned = cleaned.replace('~', '')  # Remove tilde characters
        cleaned = cleaned.replace('~~', '')  # Remove double tildes
        cleaned = re.sub(r'\s+fe\s*$', '', cleaned)  # Remove "fe" at end of lines
        cleaned = re.sub(r'\s+[A-Z]{1,2}\s*$', '', cleaned)  # Remove single/double letters at end
        cleaned = re.sub(r'\s+[^A-Za-z0-9\s\.]+$', '', cleaned)  # Remove symbols at end of lines
        
        # Additional OCR cleaning
        cleaned = re.sub(r'(\d+\.\d+)\s+(\d+)', r'\1', cleaned)
        cleaned = re.sub(r'(\d+\.\d+)I', r'\1', cleaned)
        
        # Split into lines for processing
        lines = cleaned.split('\n')
        
        # Clean each line individually
        cleaned_lines = []
        for line in lines:
            # Remove common OCR artifacts that interfere with detection
            line = line.replace('~', '')  # Remove tilde characters
            line = line.replace('~~', '')  # Remove double tildes
            line = re.sub(r'\s+fe\s*$', '', line)  # Remove "fe" at end of lines
            line = re.sub(r'\s+[A-Z]{1,2}\s*$', '', line)  # Remove single/double letters at end
            line = re.sub(r'\s+[^A-Za-z0-9\s\.]+$', '', line)  # Remove symbols at end of lines
            cleaned_lines.append(line)
        
        # Combine split player prop lines (e.g., "CARLOS NARVAEZ\nOVER 1.5 TOTAL BASES")
        combined_lines = []
        i = 0
        while i < len(cleaned_lines):
            current_line = cleaned_lines[i]
            # Merge 'Player 1+ +odds' with next 'ALT Home Runs' or 'ALT Home Run' line
            if re.match(r"[A-Za-z .'-]+\s+1\+\s*\+?\d+", current_line) and i + 1 < len(cleaned_lines):
                next_line = cleaned_lines[i + 1]
                if next_line.strip().upper() in ["ALT HOME RUNS", "ALT HOME RUN"]:
                    # Remove odds from current_line
                    player_part = re.sub(r"\s*\+\d+$", "", current_line)
                    merged = f"{player_part} Home Runs"
                    combined_lines.append(merged)
                    i += 2
                    continue
            # Merge player name + 1+ with next line if it's a stat type
            if (current_line.isupper() and not any(char.isdigit() for char in current_line) and len(current_line.split()) <= 3 and i + 1 < len(cleaned_lines)):
                next_line = cleaned_lines[i + 1]
                if re.search(r'(over|under|o|u)\s+\d+\.?\d*\s+[a-zA-Z\s]+', next_line, re.IGNORECASE):
                    combined_line = f"{current_line} {next_line}"
                    combined_lines.append(combined_line)
                    i += 2
                    continue
            # Handle ParlayScience format: "PLAYER NAME" followed by "X TO HIT A HOME RUN"
            if (current_line.isupper() and 
                len(current_line.split()) <= 3 and 
                not any(char in current_line for char in ['+', '-', '$', '%']) and
                i + 1 < len(cleaned_lines)):
                next_line = cleaned_lines[i + 1]
                if re.search(r'[A-Z]\s+TO\s+HIT\s+A?\s*(HOME RUN|Home Run)', next_line, re.IGNORECASE):
                    # Combine player name with the bet
                    combined_line = f"{current_line} {next_line}"
                    combined_lines.append(combined_line)
                    i += 2
                    continue
            # Handle ParlayScience format: "PLAYER NAME" followed by "2+ TOTAL BASES"
            if (current_line.isupper() and 
                len(current_line.split()) <= 3 and 
                not any(char in current_line for char in ['+', '-', '$', '%', '\\', '/']) and
                i + 1 < len(cleaned_lines)):
                next_line = cleaned_lines[i + 1]
                if re.search(r'\d+\+\s*(TOTAL BASES|Total Bases)', next_line, re.IGNORECASE):
                    # Combine player name with the bet
                    combined_line = f"{current_line} {next_line}"
                    combined_lines.append(combined_line)
                    i += 2
                    continue
            # Handle cases where player name has extra characters but bet is on next line
            if (current_line.isupper() and 
                len(current_line.split()) <= 4 and  # Allow slightly longer names
                not any(char in current_line for char in ['+', '-', '$', '%', '\\', '/']) and
                i + 1 < len(cleaned_lines)):
                next_line = cleaned_lines[i + 1]
                # More flexible pattern to match "2+ TOTALBASES" or "2+ TOTAL BASES"
                if re.search(r'\d+\+\s*(TOTAL\s*BASES?|Total\s*Bases?)', next_line, re.IGNORECASE):
                    # Clean up the player name by removing extra characters
                    clean_player_name = re.sub(r'\s+[a-z]{1,2}\s*$', '', current_line).strip()
                    combined_line = f"{clean_player_name} {next_line}"
                    combined_lines.append(combined_line)
                    i += 2
                    continue
            combined_lines.append(current_line)
            i += 1
        return '\n'.join(combined_lines)
    
    def process_image_url(self, image_url: str) -> Optional[str]:
        """
        Downloads an image and extracts text from it.
        
        Args:
            image_url: URL of the image to process
            
        Returns:
            Extracted text, or None if processing failed
        """
        image_path = self.download_image(image_url)
        if not image_path:
            return None
        
        return self.extract_text_from_image(image_path)

# Global instance for reuse
image_processor = ImageProcessor() 