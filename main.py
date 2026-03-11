#!/usr/bin/env python3
import argparse
import sys
from src.obfuscator import LuaObfuscator

def main():
    parser = argparse.ArgumentParser(description='Roblox Lua Obfuscator')
    parser.add_argument('input', help='Input Lua file')
    parser.add_argument('-o', '--output', help='Output file', default='obfuscated.lua')
    parser.add_argument('--no-strings', action='store_true', help='Disable string encryption')
    parser.add_argument('--no-cf', action='store_true', help='Disable control flow flattening')
    parser.add_argument('--no-vm', action='store_true', help='Disable VM-based obfuscation')
    parser.add_argument('--no-anti-tamper', action='store_true', help='Disable anti-tamper')
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print(f'Error: File "{args.input}" not found')
        sys.exit(1)
    
    obfuscator = LuaObfuscator()
    
    options = {
        'encrypt_strings': not args.no_strings,
        'control_flow': not args.no_cf,
        'vm_based': not args.no_vm,
        'anti_tamper': not args.no_anti_tamper
    }
    
    print('Obfuscating...')
    obfuscated = obfuscator.obfuscate(code, **options)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(obfuscated)
    
    print(f'Done! Output saved to: {args.output}')

if __name__ == '__main__':
    main()
