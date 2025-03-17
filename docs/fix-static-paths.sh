#!/bin/bash

echo "Fixing static asset paths for GitHub Pages deployment..."

# Detect OS type for sed command
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  SED_CMD="sed -i ''"
else
  # Linux and others
  SED_CMD="sed -i"
fi

# Check if out directory exists
if [ ! -d "out" ]; then
  echo "Error: 'out' directory not found. Run the build first."
  exit 1
fi

# Fix paths in HTML files
echo "Fixing paths in HTML files..."
find out -type f -name "*.html" -exec $SED_CMD 's|src="/_next/|src="./chorus/_next/|g' {} \;
find out -type f -name "*.html" -exec $SED_CMD 's|href="/_next/|href="./chorus/_next/|g' {} \;

# Fix paths in CSS files
echo "Fixing paths in CSS files..."
find out -type f -name "*.css" -exec $SED_CMD 's|url(/_next/|url(./chorus/_next/|g' {} \;

echo "Static asset paths fixed successfully" 