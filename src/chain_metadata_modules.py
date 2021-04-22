import os
import sys
import json
import chain_metadata

BOT_MODULES = os.environ.get('BOT_MODULES')
print(BOT_MODULES)
if BOT_MODULES is None or len(BOT_MODULES) == 0:
    print("Set environment variables, \nsource ../spiderdao_env")
    sys.exit(0)

modules_filt = BOT_MODULES.split(",")

data = chain_metadata.metadata

#Chain modules in text format for help messages
botcalls_mods = {}

#Chain modules in json format for logic and filteration
chain_modules = {}

dao_functions = {
    "transfer" : "Propose Transfer",
    "propose_bounty" : "Custom Proposal",
    "award_bounty" : "Custom Proposal",
}
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
            func_name = d[c]
            if func_name not in list(dao_functions.keys()):
                continue

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
            modd = f"⚡️ {func_name} {sargs} \t  💎 Help: {doc}" 
            botcalls_mods[modid].append(modd)
            chain_modules[modid][func_name] = {}
            chain_modules[modid][func_name]["args"] = jrgs
            chain_modules[modid][func_name]["doc"] = d["documentation"]
            chain_modules[modid][func_name]["display_name"] = dao_functions[func_name]
            chain_modules[modid][func_name]["func_name"] = func_name

