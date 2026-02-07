import csv
import json
import csv
import sys

# with open("2parsedHOS.json", "r") as f1:
#     # Use json.load() for files, not json.loads()
#     # Assuming the JSON is a list of objects, we load it directly
#     data = json.load(f1)
    
#     # Verify we have data before proceeding
#     if data:
#         # Get headers from the first dictionary keys
#         headers = data[0].keys()

#         # Write to a file
#         with open('output.csv', 'w', newline='') as f:
#             writer = csv.DictWriter(f, fieldnames=headers)
#             writer.writeheader()
#             writer.writerows(data)
            
#         print("Successfully wrote output.csv")
#     else:
#         print("JSON file was empty or list was empty.")
import csv
import json

# 1. Added encoding='utf-8' to handle special characters in the source
with open("2parsedHOS.json", "r", encoding='utf-8') as f1:
    data = json.load(f1)
    
    if data:
        headers = data[0].keys()

        # 2. Added encoding='utf-8' here to prevent the 'charmap' crash
        with open('output.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
            
        print("Successfully wrote output.csv")
    else:
        print("JSON file was empty or list was empty.")