#!/usr/bin/env python3
"""
Script để convert PyQt6 imports sang PySide6 cho macOS build
PySide6 tương thích với PyQt6 về API, chỉ khác imports
"""

import sys
import re
from pathlib import Path

def convert_pyqt6_to_pyside6(input_file, output_file):
    """Convert PyQt6 imports to PySide6"""
    
    print(f"[*] Converting {input_file} to use PySide6...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace PyQt6 imports with PySide6
    replacements = [
        (r'from PyQt6\.', 'from PySide6.'),
        (r'import PyQt6\.', 'import PySide6.'),
        (r'PyQt6\.', 'PySide6.'),
        # Signal names: pyqtSignal -> Signal
        (r'pyqtSignal', 'Signal'),
        # QApplication.exec() -> QApplication.exec_() (PySide6 uses exec_)
        # Actually, both use exec() in newer versions, so no change needed
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write output
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[+] Converted to {output_file}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: convert_pyqt6_to_pyside6.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not Path(input_file).exists():
        print(f"[!] Error: {input_file} not found")
        sys.exit(1)
    
    convert_pyqt6_to_pyside6(input_file, output_file)

