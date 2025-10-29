#!/bin/bash

# Find all HTML files except system files
files=$(find . -name "*.html" -not -name "404.html" -not -name "401.html" -not -name "detail_collection-1.html" -not -name "style-guide.html")

for file in $files; do
  if [ -f "$file" ]; then
    echo "Updating $file..."
    
    # Update Work link - handle both https://Work and href="#"
    sed -i '' 's|href="https://Work"|href="index.html"|g' "$file"
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>Work</p>|href="index.html" class="w-inline-block">\n                  <p>Work</p>|g' "$file"
    
    # Update Services link
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>Services</p>|href="services.html" class="w-inline-block">\n                  <p>Services</p>|g' "$file"
    
    # Update About link
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>About</p>|href="about.html" class="w-inline-block">\n                  <p>About</p>|g' "$file"
    
    # Update Contact link
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>Contact</p>|href="contact.html" class="w-inline-block">\n                  <p>Contact</p>|g' "$file"
  fi
done

echo "All navbar links updated!"
