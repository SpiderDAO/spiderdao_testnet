#!/bin/bash

mkdir -p docs
cp api/README.md docs/README_spiderdao_api.md
cp chainspec/README.md docs/README_chainspecs.md
cp db/README.md docs/README_db.md
cp discord_bot/README.md docs/README_spider_discord_bot.md
cp examples/README.md docs/README_propose_example.md
cp -r imgs/*  docs/diagrams/
cp nginx/README.md docs/README_nginx.md
cp scripts/README.md docs/README_scripts.md
cp src/README.md docs/README_spiderdao.md
cp tests/README.md docs/README_tests.md
cp trackchanges/spider_changes.md docs/spider_changes.md
cp README.md docs/README_full.md