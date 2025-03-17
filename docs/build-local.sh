#!/bin/bash

# Check if nvm is installed
if [ -s "$HOME/.nvm/nvm.sh" ]; then
  source "$HOME/.nvm/nvm.sh"
  
  # Use Node.js 22 for the build
  echo "Switching to Node.js 22..."
  nvm use 22 || nvm install 22
  
  # Install dependencies if needed
  if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm ci
  fi
  
  # Update browserslist database
  echo "Updating browserslist database..."
  npx update-browserslist-db@latest
  
  # Run the build with more verbose output
  echo "Building the documentation site..."
  NODE_OPTIONS="--trace-warnings" npm run build
  
  # Check build result
  if [ $? -eq 0 ]; then
    echo "Build completed successfully. Check the 'out' directory for the generated files."
  else
    echo "Build failed. Please check the error messages above."
  fi
else
  echo "NVM (Node Version Manager) is not installed. Please install NVM or manually switch to Node.js 22 before running this script."
  exit 1
fi 