#!/bin/bash

# Display current Node.js version
echo "Using Node.js version: $(node -v)"

# Update browserslist database
echo "Updating browserslist database..."
npx update-browserslist-db@latest

# Run the build with more verbose output
echo "Building the documentation site..."
NODE_OPTIONS="--trace-warnings" npm run build

# Check build result
if [ $? -eq 0 ]; then
  echo "Build completed successfully."
  
  # Check if the output directory exists and list its contents
  if [ -d "out" ]; then
    echo "Output directory exists. Contents:"
    ls -la out
    echo "Number of files in output directory: $(find out -type f | wc -l)"
  else
    echo "Warning: Output directory 'out' does not exist."
  fi
else
  echo "Build failed. Please check the error messages above."
fi 