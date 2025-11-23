#!/bin/bash

# Navigate to project root
cd /Users/syshin/Desktop/Syshin/apphub-ai

# Clean up
rm -rf data
mkdir -p data/blog

# Navigate to blog directory
cd data/blog

# Initialize git
git init

# Add remote
git remote add origin https://github.com/syshin0116/syshin0116.github.io.git

# Enable sparse checkout
git config core.sparseCheckout true

# Configure to only checkout content directory
mkdir -p .git/info
echo "content/" > .git/info/sparse-checkout

# Pull from main branch
git pull origin main

echo "Done! Check data/blog/content"
ls -la
