import io
import re
import sys
import tokenize

def remove_py_comments(src: str) -> str:
    out = []
    g = tokenize.generate_tokens(io.StringIO(src).readline)
    prev_end = (0, 0)
    for toknum, tokval, start, end, line in g:
        if toknum == tokenize.COMMENT:
            continue
        out.append(tokval)
    return ''.join(out)

def remove_c_style_comments(src: str) -> str:
    # remove /* ... */
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    # remove // ...\n
    src = re.sub(r"//.*", "", src)
    return src

def remove_html_comments(src: str) -> str:
    return re.sub(r"<!--([\s\S]*?)-->", "", src)

def remove_css_comments(src: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/", "", src)

def process_file(path: str):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        src = f.read()

    if path.endswith('.py'):
        new = remove_py_comments(src)
    elif path.endswith(('.js', '.jsx', '.ts', '.tsx')):
        new = remove_c_style_comments(src)
    elif path.endswith(('.html', '.htm')):
        new = remove_html_comments(src)
    elif path.endswith('.css'):
        new = remove_css_comments(src)
    else:
        print(f"Skipping unsupported file type: {path}")
        return

    if new != src:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        print(f"Stripped comments: {path}")
    else:
        print(f"No changes: {path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: remove_comments.py <file1> [file2 ...]')
        sys.exit(1)
    for p in sys.argv[1:]:
        process_file(p)
