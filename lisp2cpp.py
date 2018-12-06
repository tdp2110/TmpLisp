import re
import sys

LPAREN = '('
RPAREN = ')'

def tokenize_chunk(chunk):
    m = re.match('([\(]*)([^\(\)]*)([\)]*)$', chunk)

    for group in m.groups():
        if group:
            if '(' in group or ')' in group:
                yield from group
            else:
                yield group
    
def tokenize(text):
    for chunk in text.split():
        yield from tokenize_chunk(chunk)

def main():
    lines = sys.stdin.readlines()
    tokens = tokenize(''.join(lines))
    print('\n'.join(tokens))    
    
if __name__ == '__main__':
    main()
