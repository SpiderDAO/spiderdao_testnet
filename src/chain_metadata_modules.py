import os
import sys
import json
import chain_metadata

BOT_MODULES = os.environ.get('BOT_MODULES')
print(BOT_MODULES)
if len(BOT_MODULES) == 0:
    print("Set environment variables, \nsource ../spiderdao_env")
    sys.exit(0)

modules_filt = BOT_MODULES.split(",")

data = chain_metadata.metadata

#Chain modules in text format for help messages
botcalls_mods = {}

#Chain modules in json format for logic and filteration
chain_modules = {}

#Convert the chain modules json to a simpler format
for d in data:
    if d["module_id"] not in modules_filt:
        continue

    botcalls_mods[d["module_id"]] = []
    chain_modules[d["module_id"]] = {}

for d in data:
    if d["module_id"] not in modules_filt:
        continue
    for c in d:
        modid = d["module_id"]
        if c == "call_name":
            doc = d["documentation"]
            if "\n" in doc: #Not full documentation added to save message space
                doc = doc.split("\n")[0]
            
            margs = d["call_args"]
            mrgs = []
            jrgs = []
            for ma in margs:
                mrgs.append(ma["name"])
                jrgs.append(ma)
            
            sargs = f'({", ".join(mrgs)})'
            modd = f"⚡️ {d[c]} {sargs} \t  💎 Help: {doc}" 
            botcalls_mods[modid].append(modd)
            chain_modules[modid][d[c]] = jrgs

