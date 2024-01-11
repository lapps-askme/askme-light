import sys
import json
import subprocess
from pygments import highlight, lexers, formatters

from utils import color


urls = [
    ('help', "http://localhost:8000/api/help"),
    ('doc', "http://localhost:8000/api/doc/54b4324ee138239d8684aeb2?pretty=1"),
    ('field', "http://localhost:8000/api/doc/54b4324ee138239d8684aeb2/title"),
    ('related', "http://localhost:8000/api/related/54b4324ee138239d8684aeb2?pretty=1"),
    ('set', "http://localhost:8000/api/set?ids=54b4324ee138239d8684aeb2"),
    ('error', "http://localhost:8000/api/error")]

cases = ['all'] + [name for name, url in urls]


def print_headers(headers: str):
    for line in headers.split('\n'):
        if (line.startswith('server')
            or line.startswith('content-length')):
            continue
        print(line)

def ping_api(name, url):
    print(f'{color.BOLD}>>> {name.upper()} {url}{color.END}\n')
    result = subprocess.run(
        ['curl', '--include', '--silent', url], capture_output=True, text=True)
    #print(result.stdout)
    headers, body = result.stdout.split('\n\n', 1)
    if name == 'help':
        print(body)
    else:
        print_headers(headers)
        print()
        body = json.loads(body)
        if 'stack' in body:
            body['stack'] = body['stack'][-2:]
        if 'exception' in body and 'stack' in body['exception']:
            body['exception']['stack'] = body['exception']['stack'][-1:]
        output = json.dumps(body, indent=2)
        output = highlight(output, lexers.JsonLexer(), formatters.TerminalTrueColorFormatter())
        print(output)


if __name__ == '__main__':

    case_name = sys.argv[1] 
    if not case_name in cases:
        print(f"Warning: unknown test case, use one of {cases}")
    if case_name != 'all':
        print()
    for name, url in urls:
        if name == case_name or case_name == 'all':
            ping_api(name, url)
