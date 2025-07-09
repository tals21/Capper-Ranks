#!/usr/bin/env python3
"""
Debug script to test line combining logic with ParlayScience OCR output.
"""

import sys
import os
import re

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from capper_ranks.services.image_processor import image_processor

def test_line_combining():
    """Test the line combining logic with ParlayScience OCR output."""
    
    # Simulate the OCR output from the ParlayScience tweet
    ocr_text = """BASES PARLAY
ALS
\\Y
+/89 (a
V
\\/
SHOHEI OHTANI 2+  TOTAL BASES
VLADIMIR GUERRERO JR.  2+  TOTAL BASES
JOSE RAMIREZ fe
2+  TOTALBASES 
JOIN TODAY AT
PARLAYSCIENCE.COM
Sie ff ee ,. * 2"""
    
    print("Original OCR text:")
    print(ocr_text)
    print("\n" + "="*50 + "\n")
    
    # Test the line combining logic
    lines = ocr_text.split('\n')
    combined_lines = []
    i = 0
    
    print("Processing lines:")
    while i < len(lines):
        current_line = lines[i]
        print(f"Line {i}: '{current_line}'")
        
        # Handle ParlayScience format: "PLAYER NAME" followed by "2+ TOTAL BASES"
        if (current_line.isupper() and 
            len(current_line.split()) <= 3 and 
            not any(char in current_line for char in ['+', '-', '$', '%', '\\', '/']) and
            i + 1 < len(lines)):
            next_line = lines[i + 1]
            print(f"  Checking next line: '{next_line}'")
            if re.search(r'\d+\+\s*(TOTAL BASES|Total Bases)', next_line, re.IGNORECASE):
                print(f"  ✅ MATCH: Combining '{current_line}' with '{next_line}'")
                combined_line = f"{current_line} {next_line}"
                combined_lines.append(combined_line)
                i += 2
                continue
        
        # Handle cases where player name has extra characters but bet is on next line
        if (current_line.isupper() and 
            len(current_line.split()) <= 4 and  # Allow slightly longer names
            not any(char in current_line for char in ['+', '-', '$', '%', '\\', '/']) and
            i + 1 < len(lines)):
            print(f"  ✅ Line passes all conditions for extra chars check")
            next_line = lines[i + 1]
            print(f"  Checking next line for extra chars: '{next_line}'")
            
            # Test multiple regex patterns
            patterns = [
                r'\d+\+\s*(TOTAL\s*BASES?|Total\s*Bases?)',
                r'\d+\+\s*TOTAL\s*BASES',
                r'\d+\+\s*TOTALBASES',
                r'\d\+\s*TOTAL\s*BASES',
                r'\d\+\s*TOTALBASES'
            ]
            
            for pattern in patterns:
                if re.search(pattern, next_line, re.IGNORECASE):
                    print(f"  ✅ MATCH with pattern '{pattern}': Combining '{current_line}' with '{next_line}'")
                    # Clean up the player name by removing extra characters
                    clean_player_name = re.sub(r'\s+[a-z]{1,2}\s*$', '', current_line).strip()
                    combined_line = f"{clean_player_name} {next_line}"
                    combined_lines.append(combined_line)
                    i += 2
                    break
            else:
                print(f"  ❌ NO MATCH: '{next_line}' doesn't match any pattern")
                combined_lines.append(current_line)
                i += 1
                continue
        else:
            print(f"  ❌ Line doesn't pass conditions:")
            print(f"    - isupper(): {current_line.isupper()}")
            print(f"    - len <= 4: {len(current_line.split()) <= 4}")
            print(f"    - no special chars: {not any(char in current_line for char in ['+', '-', '$', '%', '\\\\', '/'])}")
            print(f"    - has next line: {i + 1 < len(lines)}")
        
        combined_lines.append(current_line)
        i += 1
    
    print("\n" + "="*50 + "\n")
    print("Combined result:")
    print('\n'.join(combined_lines))

if __name__ == '__main__':
    test_line_combining() 