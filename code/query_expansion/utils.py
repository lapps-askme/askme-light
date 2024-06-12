import re


# https://stackoverflow.com/questions/12507206/how-to-completely-traverse-a-complex-dictionary-of-unknown-depth#12507546

def dict_generator(indict, pre=None):
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in dict_generator(value, pre + [key]):
                    yield d
            elif isinstance(value, list) or isinstance(value, tuple):
                for v in value:
                    for d in dict_generator(v, pre + [key]):
                        yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [indict]


# https://stackoverflow.com/questions/68200973/highlight-multiple-substrings-in-a-string-in-python

def highlight(text: str, words: list):
    highlight_str = r"\b(?:" + '|'.join(words) + r")\b"
    return re.sub(highlight_str, '\033[44;33m\g<0>\033[m', text)
