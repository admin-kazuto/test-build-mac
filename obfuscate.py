#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Python Obfuscator - Làm rối code để chống dịch ngược
Không cần license, hoàn toàn miễn phí
"""

import re
import random
import string
import base64
import ast
import sys
from pathlib import Path


class CodeObfuscator:
    def __init__(self):
        self.var_map = {}
        self.func_map = {}
        self.class_map = {}
        self.counter = 0
        self.string_encodings = []
        
    def _generate_random_name(self, prefix='_'):
        """Tạo tên ngẫu nhiên cho biến/func/class"""
        self.counter += 1
        # Tạo tên dài và khó đọc
        chars = string.ascii_letters + string.digits
        length = random.randint(12, 20)
        name = prefix + ''.join(random.choice(chars) for _ in range(length))
        # Tránh trùng với keywords
        if name in ['if', 'for', 'while', 'def', 'class', 'import', 'from', 'return', 'True', 'False', 'None']:
            return self._generate_random_name(prefix)
        return name
    
    def _encode_string(self, s):
        """Encode string thành base64 hoặc hex"""
        if len(s) < 3:
            return s
        method = random.choice(['base64', 'hex', 'chr'])
        if method == 'base64':
            encoded = base64.b64encode(s.encode()).decode()
            return f"base64.b64decode('{encoded}').decode()"
        elif method == 'hex':
            encoded = s.encode().hex()
            return f"bytes.fromhex('{encoded}').decode()"
        else:  # chr
            encoded = '+'.join(f"chr({ord(c)})" for c in s)
            return f"({encoded})"
    
    def _obfuscate_strings(self, code):
        """Obfuscate string literals"""
        # Đơn giản hóa: chỉ encode một số strings quan trọng
        # Tránh encode docstrings và strings trong imports
        lines = code.split('\n')
        result = []
        in_docstring = False
        
        for line in lines:
            # Bỏ qua docstrings
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                result.append(line)
                continue
            if in_docstring:
                result.append(line)
                continue
            
            # Tìm và encode string literals đơn giản (trong quotes)
            def replace_simple_string(m):
                s = m.group(0)
                # Bỏ qua nếu là import hoặc comment
                if 'import' in line or line.strip().startswith('#'):
                    return s
                # Chỉ encode strings dài hơn 5 ký tự
                if len(s) > 7 and random.random() > 0.5:
                    try:
                        # Lấy nội dung string (bỏ quotes)
                        content = s[1:-1]  # Bỏ quotes đầu và cuối
                        if content and not content.startswith('http'):  # Bỏ qua URLs
                            encoded = self._encode_string(content)
                            return encoded
                    except:
                        pass
                return s
            
            # Match string literals đơn giản
            line = re.sub(r'["\']([^"\']{5,})["\']', replace_simple_string, line)
            result.append(line)
        
        return '\n'.join(result)
    
    def _obfuscate_names(self, code):
        """Đổi tên biến, function, class"""
        # Parse AST để tìm tất cả names
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Nếu parse lỗi, bỏ qua obfuscation names
            print("[!] Khong the parse AST, bo qua obfuscation names")
            return code
        
        class NameCollector(ast.NodeVisitor):
            def __init__(self):
                self.names = set()
                self.funcs = set()
                self.classes = set()
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    self.names.add(node.id)
            
            def visit_FunctionDef(self, node):
                self.funcs.add(node.name)
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                self.classes.add(node.name)
                self.generic_visit(node)
        
        collector = NameCollector()
        try:
            collector.visit(tree)
        except:
            return code
        
        # Tạo mapping (giữ lại một số tên quan trọng)
        protected = {
            'self', 'sys', 'os', 'time', 'json', 'requests', 'threading',
            'QApplication', 'QMainWindow', 'QWidget', 'QVBoxLayout',
            '__init__', '__name__', '__main__', '__file__', '__doc__',
            'print', 'len', 'str', 'int', 'dict', 'list', 'tuple',
            'True', 'False', 'None', 'Exception', 'BaseException',
            'Qt', 'QObject', 'pyqtSignal', 'QThread', 'QRunnable'
        }
        
        # Map functions (chỉ những tên dài và không protected)
        for func_name in collector.funcs:
            if (func_name not in protected and 
                not func_name.startswith('_') and 
                len(func_name) > 4 and
                func_name not in self.func_map):
                self.func_map[func_name] = self._generate_random_name('_fn')
        
        # Map classes
        for class_name in collector.classes:
            if (class_name not in protected and 
                not class_name.startswith('_') and
                class_name not in self.class_map):
                self.class_map[class_name] = self._generate_random_name('_cls')
        
        # Map variables (chỉ những tên dài)
        for var_name in collector.names:
            if (var_name not in protected and 
                not var_name.startswith('_') and 
                len(var_name) > 5 and
                var_name not in self.var_map):
                self.var_map[var_name] = self._generate_random_name('_var')
        
        # Replace names trong code (theo thứ tự: classes -> functions -> variables)
        # Classes
        for old, new in sorted(self.class_map.items(), key=lambda x: -len(x[0])):
            code = re.sub(r'\b' + re.escape(old) + r'\b', new, code)
        
        # Functions
        for old, new in sorted(self.func_map.items(), key=lambda x: -len(x[0])):
            code = re.sub(r'\b' + re.escape(old) + r'\b', new, code)
        
        # Variables (cẩn thận hơn)
        for old, new in sorted(self.var_map.items(), key=lambda x: -len(x[0])):
            # Chỉ replace khi không phải là attribute
            code = re.sub(r'(?<!\.)\b' + re.escape(old) + r'\b(?!\s*[\.\(])', new, code)
        
        return code
    
    def _add_dead_code(self, code):
        """Thêm dead code để làm rối"""
        dead_code_snippets = [
            "if False:\n    _ = lambda x: x + 1\n    _ = sum(range(100))\n",
            "if 0:\n    _tmp = [i for i in range(1000)]\n    del _tmp\n",
            "if not True:\n    _dummy = {'a': 1, 'b': 2}\n    _dummy.clear()\n",
        ]
        
        # Thêm dead code vào đầu một số functions
        lines = code.split('\n')
        result = []
        i = 0
        while i < len(lines):
            result.append(lines[i])
            # Thêm dead code sau def statements (30% chance)
            if lines[i].strip().startswith('def ') and random.random() < 0.3:
                indent = len(lines[i]) - len(lines[i].lstrip())
                dead = random.choice(dead_code_snippets)
                dead_lines = dead.split('\n')
                for dl in dead_lines:
                    if dl.strip():
                        result.append(' ' * (indent + 4) + dl)
            i += 1
        
        return '\n'.join(result)
    
    def _flatten_control_flow(self, code):
        """Làm phẳng control flow (đơn giản hóa)"""
        # Thay một số if-else bằng ternary operators
        # (chỉ áp dụng cho các case đơn giản)
        pattern = r'if\s+(\w+)\s*:\s*\n\s+(\w+)\s*=\s*([^;\n]+)\s*\n\s+else\s*:\s*\n\s+\2\s*=\s*([^;\n]+)'
        def replace_ternary(match):
            var = match.group(1)
            assign_var = match.group(2)
            true_val = match.group(3)
            false_val = match.group(4)
            return f"{assign_var} = {true_val} if {var} else {false_val}"
        
        code = re.sub(pattern, replace_ternary, code, flags=re.MULTILINE)
        return code
    
    def obfuscate(self, code):
        """Main obfuscation function"""
        print("[*] Bat dau obfuscate code...")
        
        # Step 1: Encode strings
        print("[*] Dang encode strings...")
        code = self._obfuscate_strings(code)
        
        # Step 2: Obfuscate names
        print("[*] Dang doi ten bien/func/class...")
        code = self._obfuscate_names(code)
        
        # Step 3: Add dead code
        print("[*] Dang them dead code...")
        code = self._add_dead_code(code)
        
        # Step 4: Flatten control flow
        print("[*] Dang lam phang control flow...")
        code = self._flatten_control_flow(code)
        
        # Step 5: Add header với imports cần thiết
        header = """# Obfuscated code - Do not modify
import base64
import sys
import os
"""
        code = header + code
        
        print("[+] Obfuscation hoan tat!")
        return code


def main():
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    if len(sys.argv) < 3:
        print("Usage: python obfuscate.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: File khong ton tai: {input_file}")
        sys.exit(1)
    
    print(f"[*] Doc file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    obfuscator = CodeObfuscator()
    obfuscated = obfuscator.obfuscate(code)
    
    print(f"[*] Ghi file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(obfuscated)
    
    print(f"[+] Hoan tat! File da duoc obfuscate: {output_file}")
    print(f"[*] Kich thuoc: {len(obfuscated)} bytes")


if __name__ == '__main__':
    main()

