import os.path
from os import path
import sys
from onepassword import OnePassword
import json
from json import JSONEncoder
from deepdiff import DeepDiff  # For Deep Difference of 2 objects
from deepdiff import grep, DeepSearch  # For finding if item exists in an object
from deepdiff import DeepHash  # For hashing objects based on their contents

# subclass JSONEncoder
class setEncoder(JSONEncoder):
    def default(self, obj):
        return list(obj)
if len(sys.argv) < 3:
    print("please provide names of two vaults to compare")
    sys.exit()
if len(sys.argv) > 3:
    print("please provide names of only two vaults to compare")
    sys.exit()
vaultA, vaultB= sys.argv[1], sys.argv[2]
if(path.exists('.op/config')):
    with open('.bashrc', 'a') as file:
        file.write('export OP_DEVICE=yqxxxxxxxxxa34qltjhfrvdx2a\n')
        file.write('export OP_SESSION_parksidesecuritiespoc=8958WfPy44mXXXXXX7x386pg7hJQvxdzEpRCk3IXFR4\n')
op = OnePassword()
x, y = op.list_items(vaultA), op.list_items(vaultB) 
xx, yy = set(i["overview"]["title"] for i in x), set(i["overview"]["title"] for i in y)
data = {}
data[vaultA] = sorted(xx-yy)
data[vaultB] = sorted(yy-xx)
data["common"] = sorted(xx&yy)
print(json.dumps(data, indent=2, cls=setEncoder))
def op_item_json_cleanup(m, remove_list):
    if('details' in m):
        mm = m['details']
        if 'sections' in mm and len(mm['sections'])>0:
            for i in range(len(mm['sections'])):
                if 'fields' in mm['sections'][i] and len(mm['sections'][i]['fields'])>0:
                    mmm = mm['sections'][i]['fields']
                    mmm.sort(key = lambda json: json['t'], reverse=True)
                    mmmm = list(filter(lambda i: i['k'] != 'date', mmm))
                    mmm = mmmm
                    for mi in mmm:
                        [mi.pop(k, None) for k in remove_list]
        return(mm)
    return({})
            
rem_list = ['a','v','n','inputTraits']
for item in sorted(xx&yy):
    xxx, yyy = op.get_item(uuid=op.get_uuid(item, vault=vaultA)), op.get_item(uuid=op.get_uuid(item, vault=vaultB))
    xxxx, yyyy = op_item_json_cleanup(xxx, rem_list), op_item_json_cleanup(yyy, rem_list)
    thediff = DeepDiff(xxxx, yyyy, ignore_order=True, report_repetition=True)
    print("{}: {}".format(item, thediff))


