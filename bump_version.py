import os

target_dir = r"C:\Zentra-Core"
count = 0

for root, _, files in os.walk(target_dir):
    if 'venv' in root or '.git' in root or 'node_modules' in root or 'tmp' in root or '__pycache__' in root or 'logs' in root:
        continue
    for f in files:
        if f.endswith('.md') or f.endswith('.py') or f.endswith('.toml') or f.endswith('.html') or f == 'version':
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                new_content = content.replace("0.15.1", "0.15.1")
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    count += 1
                    print(f"Updated: {path}")
            except Exception:
                pass

print(f"Total files updated: {count}")
