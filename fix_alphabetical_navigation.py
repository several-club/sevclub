#!/usr/bin/env python3

import os

# Define all case files in alphabetical order
case_order = [
    "backfabrik.html",
    "bailet.html", 
    "blankens.html",
    "bord.html",
    "cervera.html",
    "claes-dalen.html",
    "coop-port-73.html",
    "coop-skargarden.html",
    "cucina-povera.html",
    "gallno.html",
    "goalplan.html",
    "hyper-island.html",
    "jeanerica.html",
    "lindbergs.html",
    "modha.html",
    "remm.html",
    "snacka-om-sjukt.html",
    "stefan-ekengren.html",
    "stelly.html",
    "universal-music.html"
]

def get_next_case(current_case):
    try:
        index = case_order.index(current_case)
        if index + 1 < len(case_order):
            return case_order[index + 1]
        else:
            # Loop back to first case (infinite loop)
            return case_order[0]
    except ValueError:
        return "index.html"

def update_alphabetical_navigation(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found")
        return
    
    # Read file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get next case in alphabetical order
    next_case = get_next_case(filename)
    
    # Create new navigation with correct alphabetical linking
    new_nav = f'''            <!-- Index/Next Navigation -->
            <div id="w-node-_720109b7-afd7-6a70-73cc-7f2fa5243625-e771b6c4" class="index-next-block">
              <a href="index.html" class="index w-inline-block">
                <p>↑ Index</p>
              </a>
              <a href="{next_case}" class="next w-inline-block">
                <p>Next →</p>
              </a>
            </div>'''
    
    # Find and replace the existing navigation
    if "index-next-block" in content:
        # Find the start and end of the navigation block
        start_marker = '            <!-- Index/Next Navigation -->'
        end_marker = '            </div>'
        
        # Find the start position
        start_pos = content.find(start_marker)
        if start_pos != -1:
            # Find the end position (look for the closing div after the navigation)
            search_start = start_pos + len(start_marker)
            end_pos = content.find(end_marker, search_start)
            if end_pos != -1:
                # Find the actual end of the navigation block
                end_pos = content.find('</div>', end_pos) + 6
                
                # Replace the entire navigation block
                old_nav = content[start_pos:end_pos]
                new_content = content.replace(old_nav, new_nav)
                
                # Write back to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"Updated {filename} -> Next: {next_case}")
            else:
                print(f"Could not find end marker in {filename}")
        else:
            print(f"Could not find navigation in {filename}")
    else:
        print(f"No navigation found in {filename}")

# Update navigation in all case files
print("Setting up alphabetical navigation with infinite loop:")
print("Alphabetical order:", " -> ".join(case_order) + " -> " + case_order[0] + " (loops)")
print("")

for case_file in case_order:
    update_alphabetical_navigation(case_file)

print("")
print("✅ Alphabetical navigation with infinite loop set up!")
print("📋 Navigation flow:")
for i, case in enumerate(case_order):
    next_case = case_order[(i + 1) % len(case_order)]
    print(f"   {case} -> {next_case}")
