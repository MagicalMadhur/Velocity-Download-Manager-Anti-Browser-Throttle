import os
import ast
import sys
import importlib.util

def is_stdlib(module_name):
    if not module_name:
        return False
    # Get base module name
    base = module_name.split('.')[0]
    
    # Exclude known external packages and internal
    if base in ['yt_dlp', 'websockets', 'mutagen', 'secretstorage', 'brotli', 'certifi', 'cryptography', 'requests', 'urllib3']:
        return False
        
    try:
        spec = importlib.util.find_spec(base)
        if spec is None:
            return False
        # If it's in site-packages, it's not stdlib
        if spec.origin and 'site-packages' in spec.origin:
            return False
        return True
    except Exception:
        return False

yt_dlp_path = r"C:\Users\MDC\AppData\Roaming\Python\Python310\site-packages\yt_dlp"

imports = set()

for root, _, files in os.walk(yt_dlp_path):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if is_stdlib(alias.name):
                                    imports.add(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and is_stdlib(node.module):
                                imports.add(node.module)
                except SyntaxError:
                    pass

print("FOUND STDLIB IMPORTS:")
for imp in sorted(imports):
    print(imp)

with open("stdlib_imports.txt", "w") as f:
    for imp in sorted(imports):
        f.write(imp + "\n")
