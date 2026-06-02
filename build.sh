#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Self-heal blog featured images. Any post whose stored image file is missing
# from the configured storage backend (e.g. lost from the old ephemeral disk)
# gets a fresh Pexels image saved through Django storage — which, with
# CLOUDINARY_URL set, lands in Cloudinary and persists across future deploys.
# This is a no-op once every image is present, and never fails the build.
python manage.py refetch_blog_images || echo "refetch_blog_images skipped (non-fatal)"
