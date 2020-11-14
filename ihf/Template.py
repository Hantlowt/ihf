import re
from bs4 import BeautifulSoup as bs
import html


def open_template(template):
    with open(template) as f:
        result = f.read()
        f.close()
    result = convert_template(result)
    result = re.sub('(?<={%)(.*)(?=%})', lambda x: open_template(x.group()), result)
    result = result.replace('{%', '').replace('%}', '')
    return result


def convert_for(full, attr):
    attr_split = attr.split(' in ')
    var = attr_split[0].strip()
    list = attr_split[1].strip()
    full = full.replace('for="' + html.escape(attr) + '"', '')
    result = '${' + list + '.map((' + var + ') => `' + full + '`).join(\'\')}'
    return result


def convert_if(full, attr):
    full = full.replace('if="' + html.escape(attr) + '"', '')
    result = '${' + attr + ' ? `' + full + '` : \'\'}'
    return result


def split_html_tag(full):
    start = full[:full.index('>') + 1]
    full_reverse = full[::-1]
    end = full_reverse[:full_reverse.index('<') + 1][::-1]
    content = full.replace(start, '').replace(end, '')
    return start, content, end


def convert_template(template):
    template = template.replace('{{', '${').replace('}}', '}')
    soup = bs(template, features="lxml")
    result = str(soup)
    for t in soup.html.find_all(recursive=True):
        if 'if' in t.attrs.keys():
            full = str(t)
            result = result.replace(full, convert_if(full, t.attrs['if']))
        if 'for' in t.attrs.keys():
            full = str(t)
            # start, content, end = split_html_tag(full)
            result = result.replace(full, convert_for(full, t.attrs['for']))
    return result
