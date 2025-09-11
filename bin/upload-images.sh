#!/usr/bin/env bash

# Upload images to our public access Web1 bucket.
#
# Upload a local directory of files to a Web1 S3 bucket
# and make them publicly readable.

BUCKET_NAME="lifjellopp"
LOCAL_DIR="/Users/bn/Contexts/Skarphedin/Lifjell opp 2025/Site/static/gallery"
ENDPOINT_URL="https://www.s3.eu-north.cloud.web1.fi"
AWS_ACCESS_KEY_ID="op://Private/Web1 access key/username"
AWS_SECRET_ACCESS_KEY="op://Private/Web1 access key/credential"

export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY

# Sync local dir to bucket, setting public-read ACL
op run -- aws s3 sync "$LOCAL_DIR" "s3://$BUCKET_NAME/" \
  --endpoint-url "$ENDPOINT_URL" \
  --acl public-read \
  --delete

echo "Files uploaded. Public URL base (example):"
echo "$ENDPOINT_URL/$BUCKET_NAME/"
