#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Clear references to featured images that no longer exist in storage (Render's
# MEDIA disk is wiped on every deploy). Keeps blog posts from rendering broken
# <img> tags. Non-fatal: a failure here must never block a deploy.
python manage.py prune_dead_featured_images || echo "prune_dead_featured_images failed (non-fatal)"
