#!/usr/bin/env python3
import sys
import re

def bump_version(new_version, message):
    file_path = '../index.html'
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Update subtitle
        content = re.sub(
            r'(<span class="version-subtitle" onclick="toggleVersionHistory\(\)">)v[0-9\.]+?([^<]+)?(</span>)',
            rf'\g<1>v{new_version}\3',
            content
        )
        
        # Add to history
        history_entry = f'        <b>v{new_version}</b> - {message}<br>\n'
        content = re.sub(
            r'(<div id="versionHistory" [^>]+>\s*<div[^>]+>.*?</div>\n)',
            rf'\1{history_entry}',
            content,
            flags=re.DOTALL
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
            
        print(f"Successfully bumped version to v{new_version}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bump_version.py <version> <message>")
        print("Example: python bump_version.py 3.0.2 'Fixed a bug'")
        sys.exit(1)
        
    bump_version(sys.argv[1], sys.argv[2])
