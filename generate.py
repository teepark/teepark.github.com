#!/usr/bin/env python
"""
part of this module was extracted from django (truncate_html_words() from
django/util/text.py). this is django's license:

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from datetime import datetime
import glob
import os
import re
import shutil

import mako.lookup, mako.template
import markdown


re_words = re.compile(r'&.*?;|<.*?>|(\w[\w-]*)', re.U)
re_tag = re.compile(r'<(/)?([^ ]+?)(?: (/)| .*?)?>')

TEASER_SIZE = 30
TEASER_COUNT = 5

def truncate_html_words(s, num):
    length = int(num)
    if length <= 0:
        return u''
    html4_singlets = (u'br', u'col', u'link', u'base', u'img', u'param',
            u'area', u'hr', 'input')
    pos = 0
    ellipsis_pos = 0
    words = 0
    open_tags = []
    while words <= length:
        m = re_words.search(s, pos)
        if not m:
            break
        pos = m.end(0)
        if m.group(1):
            words += 1
            if words == length:
                ellipsis_pos = pos
            continue
        tag = re_tag.match(m.group(0))
        if not tag or ellipsis_pos:
            continue
        closing_tag, tagname, self_closing = tag.groups()
        tagname = tagname.lower()
        if self_closing or tagname in html4_singlets:
            pass
        elif closing_tag:
            try:
                i = open_tags.index(tagname)
            except ValueError:
                pass
            else:
                open_tags = open_tags[i+1:]
        else:
            open_tags.insert(0, tagname)
    if words <= length:
        return s
    out = s[:ellipsis_pos] + u' ...'
    for tag in open_tags:
        out += u'</%s>' % tag
    return out

def main():
    os.chdir(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates"))

    lookup = mako.lookup.TemplateLookup(['.'])
    entry = mako.template.Template(filename="entry.html", lookup=lookup)

    excerpts = []

    if os.path.isdir("../entries"):
        shutil.rmtree("../entries")

    for path in glob.glob("../src/*.markdown"):
        name = path[path.rfind("/") + 1:path.rfind(".")]
        date = datetime.fromtimestamp(os.stat(path).st_mtime)

        with open(path) as fp:
            text = markdown.markdown(fp.read().decode('utf8'),
                    output_format='html4')

        destination = "../entries/%s/%s.html" % (
                date.strftime("%y/%b/%d").lower(), name)

        excerpts.append((date, name.replace("-", " "), destination[2:],
            truncate_html_words(text, TEASER_SIZE)))

        destfolder = os.path.dirname(os.path.abspath(destination))
        if not os.path.isdir(destfolder):
            os.makedirs(destfolder)

        with open(destination, 'w') as fp:
            fp.write(entry.render_unicode(date=date, text=text,
                name=name.replace("-", " ")).encode('utf8'))

    excerpts.sort()

    index = mako.template.Template(filename="index.html", lookup=lookup)
    text = index.render_unicode(excerpts=excerpts[:TEASER_COUNT]).encode('utf8')

    with open("../index.html", 'w') as fp:
        fp.write(text)


if __name__ == '__main__':
    main()
