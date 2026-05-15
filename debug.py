import hcl2
import json

with open('samples/after.tf') as f:
    data = hcl2.load(f)

print(json.dumps(data, indent=2, default=str))