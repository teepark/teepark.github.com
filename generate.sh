#!/usr/bin/env sh

cd `cd $(dirname $0); pwd`/templates
mako-render index.html > ../index.html
