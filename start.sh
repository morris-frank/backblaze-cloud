#!/usr/bin/env bash
# rm -f .cache/shelve

# Delete Thumbnails cache deadlinks
md5sum static/thumbnails/* | awk '{ if ($1 == "70efed9da1955e97e3e7b34986557ca5") { print "rm",$2 }}' | bash

# Compile Sass
sassc static/main.scss static/main.css 

# Run sanic app
python app.py
