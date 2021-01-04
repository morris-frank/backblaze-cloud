#!/usr/bin/env bash

# Delete the folder-content list cache
rm -f .cache/ls_cache

# Delete all Thumbnails
# rm -f static/thumbnails/*

# Compile Sass
sassc static/main.scss static/main.css 

# Run sanic app
sanic server.app --host=0.0.0.0 --port=1337 --workers=1 --no-access-logs

