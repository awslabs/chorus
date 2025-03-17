#!/bin/bash

echo "Verifying file structure and imports..."

# Check if the lib directory exists
if [ -d "src/lib" ]; then
  echo "✅ src/lib directory exists"
else
  echo "❌ src/lib directory does not exist"
  exit 1
fi

# Check if navigation.js exists
if [ -f "src/lib/navigation.js" ]; then
  echo "✅ src/lib/navigation.js exists"
else
  echo "❌ src/lib/navigation.js does not exist"
  exit 1
fi

# Check if sections.js exists
if [ -f "src/lib/sections.js" ]; then
  echo "✅ src/lib/sections.js exists"
else
  echo "❌ src/lib/sections.js does not exist"
  exit 1
fi

# Check for any remaining @/lib imports
echo "Checking for any remaining @/lib imports..."
grep -r "@/lib" src/components/ && echo "❌ Found @/lib imports in components" && exit 1 || echo "✅ No @/lib imports found in components"

# Check for any remaining @/markdoc imports
echo "Checking for any remaining @/markdoc imports..."
grep -r "@/markdoc" src/components/ && echo "❌ Found @/markdoc imports in components" && exit 1 || echo "✅ No @/markdoc imports found in components"

# Check for any remaining @/components imports
echo "Checking for any remaining @/components imports..."
grep -r "@/components" src/markdoc/ && echo "❌ Found @/components imports in markdoc" && exit 1 || echo "✅ No @/components imports found in markdoc"

# Check for any remaining @/components/Icon imports in icons directory
echo "Checking for any remaining @/components/Icon imports in icons directory..."
grep -r "@/components/Icon" src/components/icons/ && echo "❌ Found @/components/Icon imports in icons directory" && exit 1 || echo "✅ No @/components/Icon imports found in icons directory"

echo "Verification complete!" 