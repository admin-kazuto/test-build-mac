#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script sử dụng Nuitka để compile Python thành native code
Nuitka compile code thành C++ rồi compile thành binary, rất khó reverse
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_nuitka():
    """Kiểm tra Nuitka đã được cài đặt chưa"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'nuitka', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[+] Nuitka đã được cài đặt: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("[!] Nuitka chưa được cài đặt")
    print("[*] Đang cài đặt Nuitka...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 'nuitka'
        ])
        print("[+] Đã cài đặt Nuitka thành công!")
        return True
    except Exception as e:
        print(f"[!] Lỗi cài đặt Nuitka: {e}")
        print("[*] Vui lòng cài đặt thủ công: pip install nuitka")
        return False


def embed_ffmpeg():
    """Embed ffmpeg vào executable"""
    ffmpeg_path = None
    
    # Tìm ffmpeg.exe
    possible_paths = [
        'ffmpeg.exe',
        'ffmpeg/ffmpeg.exe',
        'ffmpeg/bin/ffmpeg.exe',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            ffmpeg_path = path
            break
    
    if not ffmpeg_path:
        print("[!] Không tìm thấy ffmpeg.exe")
        print("[*] Vui lòng đặt ffmpeg.exe vào thư mục hiện tại")
        return None
    
    print(f"[+] Tìm thấy ffmpeg: {ffmpeg_path}")
    return ffmpeg_path


def build_with_nuitka(input_file, output_name='KuroStudio', obfuscated=False):
    """Build với Nuitka"""
    
    if not os.path.exists(input_file):
        print(f"[!] File không tồn tại: {input_file}")
        return False
    
    # Kiểm tra Nuitka
    if not check_nuitka():
        return False
    
    # Tạo thư mục build
    build_dir = Path('build_nuitka')
    build_dir.mkdir(exist_ok=True)
    
    # Nuitka command
    cmd = [
        sys.executable, '-m', 'nuitka',
        '--standalone',  # Standalone executable
        '--onefile',     # Single file output
        '--windows-icon-from-ico=NONE',  # No icon (có thể thêm icon sau)
        '--output-dir=' + str(build_dir),
        '--output-filename=' + output_name + '.exe',
        '--remove-output',  # Clean up after build
        '--assume-yes-for-downloads',  # Auto download dependencies
        '--enable-plugin=pyqt6',  # PyQt6 support
        '--include-package-data=PyQt6',  # Include PyQt6 data
        '--nofollow-import-to=test,tests',  # Exclude test modules
        '--nofollow-import-to=unittest',   # Exclude unittest
    ]
    
    # Thêm obfuscation options
    if obfuscated:
        cmd.extend([
            '--python-flag=-O',  # Optimize (remove assertions, docstrings)
            '--python-flag=-OO', # More optimization
        ])
    
    # Include ffmpeg nếu có
    ffmpeg_path = embed_ffmpeg()
    if ffmpeg_path:
        # Nuitka sẽ tự động include file nếu được import
        # Hoặc có thể copy vào thư mục build sau
        print("[*] ffmpeg sẽ được include trong build")
    
    # Add input file
    cmd.append(input_file)
    
    print("[*] Bắt đầu build với Nuitka...")
    print(f"[*] Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("[+] Build thành công!")
        
        # Copy ffmpeg vào thư mục output nếu cần
        exe_path = build_dir / (output_name + '.exe')
        if exe_path.exists():
            print(f"[+] Executable: {exe_path}")
            print(f"[+] Kích thước: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            # Copy ffmpeg vào cùng thư mục
            if ffmpeg_path:
                dest_ffmpeg = exe_path.parent / 'ffmpeg.exe'
                shutil.copy2(ffmpeg_path, dest_ffmpeg)
                print(f"[+] Đã copy ffmpeg.exe vào: {dest_ffmpeg}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[!] Lỗi build: {e}")
        return False
    except Exception as e:
        print(f"[!] Lỗi không xác định: {e}")
        return False


def main():
    # Fix encoding cho Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("Nuitka Build Script - Compile Python thanh Native Code")
    print("=" * 60)
    
    # Kiểm tra file input
    input_file = 'run_server.py'
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    # Kiểm tra có file obfuscated không - tự động sử dụng nếu có
    obfuscated_file = 'run_server_obfuscated.py'
    if os.path.exists(obfuscated_file):
        print(f"[*] Tim thay file obfuscated: {obfuscated_file}")
        print("[*] Tu dong su dung file obfuscated")
        input_file = obfuscated_file
    
    output_name = 'KuroStudio'
    if len(sys.argv) > 2:
        output_name = sys.argv[2]
    
    success = build_with_nuitka(input_file, output_name, obfuscated=('obfuscated' in input_file))
    
    if success:
        print("\n" + "=" * 60)
        print("[+] BUILD THANH CONG!")
        print("=" * 60)
        print(f"[*] Executable: build_nuitka/{output_name}.exe")
        print("[*] File da duoc compile thanh native code, rat kho reverse!")
    else:
        print("\n" + "=" * 60)
        print("[!] BUILD THAT BAI!")
        print("=" * 60)


if __name__ == '__main__':
    main()

