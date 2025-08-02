#!/bin/bash

# Copy necessary text files for deployment
echo "Copying text files for deployment..."

# Create texts directory structure
mkdir -p texts/scripture/new_testament/english/kjv
mkdir -p texts/reference/kjv_paragraphs

# Copy KJV text files
cp -r ../texts/scripture/new_testament/english/kjv/* texts/scripture/new_testament/english/kjv/

# Copy paragraph divisions
cp ../texts/reference/kjv_paragraphs/kjv_paragraph_divisions.json texts/reference/kjv_paragraphs/

echo "Text files copied successfully!"