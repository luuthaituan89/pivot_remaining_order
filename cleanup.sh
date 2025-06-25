#!/bin/bash
# Delete all files in uploads and outputs if they exist

UPLOAD_DIR="/app/uploads"
OUTPUT_DIR="/app/outputs"

# Remove files if any exist
[ "$(ls -A $UPLOAD_DIR)" ] && rm -f $UPLOAD_DIR/*
[ "$(ls -A $OUTPUT_DIR)" ] && rm -f $OUTPUT_DIR/*
