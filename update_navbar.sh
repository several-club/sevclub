#!/bin/bash

# List of HTML files to update
files=(
  "cervera.html"
  "stefan-ekengren.html" 
  "gallno.html"
  "hyper-island.html"
  "about.html"
  "contact.html"
  "goalplan.html"
  "remm.html"
  "backfabrik.html"
  "universal-music.html"
  "bailet.html"
  "lindbergs.html"
  "snacka-om-sjukt.html"
  "blankens.html"
  "modha.html"
  "shop.html"
  "coop-port-73.html"
  "stelly.html"
  "jeanerica.html"
  "jeanerica-imparfaite.html"
  "claes-dalen.html"
  "cucina-povera.html"
  "services.html"
  "coop-skargarden.html"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Updating $file..."
    # Update Work link
    sed -i '' 's|href="https://Work"|href="index.html"|g' "$file"
    # Update Services link
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>Services</p>|href="services.html" class="w-inline-block">\n                  <p>Services</p>|g' "$file"
    # Update About link  
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>About</p>|href="about.html" class="w-inline-block">\n                  <p>About</p>|g' "$file"
    # Update Contact link
    sed -i '' 's|href="#" class="w-inline-block">\s*<p>Contact</p>|href="contact.html" class="w-inline-block">\n                  <p>Contact</p>|g' "$file"
  fi
done

echo "All navbar links updated!"
