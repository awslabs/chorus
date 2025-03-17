#!/bin/bash

echo "Fixing icon imports in the icons directory..."

# Detect OS type for sed command
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  SED_CMD="sed -i ''"
else
  # Linux and others
  SED_CMD="sed -i"
fi

# Fix icon imports in all icon files
for icon_file in src/components/icons/*.jsx; do
  echo "Fixing imports in $icon_file"
  # Replace the import line directly
  $SED_CMD 's|import { DarkMode, Gradient, LightMode } from.*|import { DarkMode, Gradient, LightMode } from "../Icon"|' "$icon_file"
done

echo "Icon imports fixed successfully" 