import ast
import sys

sys.path.insert(0, '../src')
from spiderdao import *

#Change this line with every new run
val = 12 

spdao = None

#callback passed to SpiderDaoInterface initialization to listen to chain events
async def chain_events_cb(event_index, lev, ebh):
    #print(lev)
    if event_index == "1e01": #'event_id': 'Tabled'
        print("CALLED send_referendum_started")
        msg_rep, ref_dic = await spdao.send_referendum_started(lev, ebh)
        print("ref_dic", msg_rep, ref_dic)
        spdao.vote(ref_dic["ReferendumIndex"], "yes")
    
    if event_index == "1e04" or event_index == "1e05": #'event_id': 'Passed' or 'NotPassed'
        print("CALLED show_referendum_result")
        await spdao.show_referendum_result(lev, ebh)
        
    return


#Example proposal call
prop = f"Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY {val}"

#initialize SpiderDaoInterface, passing mnemonic (seed phrase) would eliminate the need to call import_wallet()
spdao = SpiderDaoInterface(node_url="ws://127.0.0.1:9945", mnemonic=None, chain_events_cb=chain_events_cb)

n_keypair = spdao.create_wallet()

spdao.set_balance(spdao.keypair.ss58_address)
balance = spdao.get_balance(spdao.keypair.ss58_address)
print("get_balance", balance)

#import_wallet: Import exisiting wallet by seed phrase
n_keypair = spdao.import_wallet("busy fluid trick sea parrot unhappy insane black bean aspect soda bubble")


proposal = spdao.pre_propose(prop)
print("pre_propose", proposal)
if "preimage_hash" not in proposal:
    print("Something wrong, probably duplicate proposal, try change val value")
    sys.exit(0)

preimage_hash = proposal["preimage_hash"]

proposal = spdao.propose(preimage_hash)
print("propose", proposal)


prop_index = proposal["PropIndex"]

proposal = spdao.second(prop_index)
print("second", proposal)

ref_index = prop_index
vote = spdao.vote(ref_index, "yes")
print("vote_result", vote) #

props = spdao.get_all_proposals()
print("get_all_proposals", props)

#ref_index = 144
ref = spdao.get_ref_info(ref_index)
print("get_ref_info", ref, type(ref))

ref = spdao.get_all_refs()
print("get_all_refs", ref, type(ref))

balance = spdao.get_balance(n_keypair.ss58_address)
print("get_balance", balance)

props = spdao.get_all_proposals()
print("get_all_proposals", props)