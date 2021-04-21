import ast
import asyncio
import os
import re
import threading
import time
import timeago
import datetime
import pickledb

from scalecodec.type_registry import load_type_registry_preset
#from scalecodec.updater import update_type_registries
from substrateinterface import Keypair, SubstrateInterface

import chain_metadata_modules

#Get chain modules in json format
chain_modules = chain_metadata_modules.chain_modules

#Get chain modules in Bot friendly format
botcalls_mods = chain_metadata_modules.botcalls_mods

# GLOBALS
CHAIN_DEC = 10**12

# Values from ../spiderdao_env
NODE_URL = os.environ.get('NODE_URL')
launch_period = os.environ.get('LAUNCH_PERIOD')
SUDO_KEY = os.environ.get('SUDO_KEY')

#Keep track of last block number
g_last_block_number = 0
lock = threading.Lock()

#Initialize proposals data dictionary
d_props = {
    "current_proposals" : 0,
    "proposals" : [],
    "proposals_idx" : []
}

class SpiderDaoInterface:
    """
    SpiderDAO Interface
    - Contains the core logic of SpiderDAO
    - Manages communication with the chain through py-substrate-interface
    - Used by spiderdao_api.py, discord_bot.py and other scripts

    """

    def __init__(self, node_url=None, keypair=None, mnemonic=None, wait_for_finalization=True, chain_events_cb=None):
        
        """
        - keypair object can be used instead of creating or import wallet
        - If mnemonic passed, implies import_wallet(mnemonic)
        - wait_for_finalization is True by default, otherwise some extrinsics fail (like vote)
        - chain_events_cb: callback function to receive chain events
        """

        self.substrate = None

        if node_url is None:
            self.node_url = NODE_URL
        else:
            self.node_url = node_url
        
        try:
            self.substrate = self.substrate_connect()
        except:
            pass
        
        self.wait_for_finalization = wait_for_finalization

        self.CHAIN_DEC = CHAIN_DEC

        if chain_events_cb is not None: #Enable chain events listener
            self.chain_events = SpiderDaoChain(node_url=self.node_url, chain_events_cb=chain_events_cb)

        if keypair is not None:
            #RECHECK validate keypair
            self.keypair = keypair

        if mnemonic is not None:
            self.keypair = self.import_wallet(mnemonic)
            if self.keypair is None:
                return None

        #Init DB
        self.proposals_db = pickledb.load('../db/proposals.db', True, False)
        self._chain_modules = chain_modules
        self.encoded_proposal = None
        self.call_ascii = None
        self.tmp_refs = []

    #Connect to the chain
    def substrate_connect(self):
        self.substrate = SubstrateInterface(
                    url=self.node_url,
                    ss58_format=42,
                    type_registry_preset="westend"
        )

        #self.substrate.update_type_registry_presets()
        return self.substrate

    #Helper function to set a specific user's balance automatically
    def set_balance(self, addr):

        self.substrate = self.substrate_connect()
        try:
            keypair = Keypair.create_from_mnemonic(SUDO_KEY)
            #keypair = Keypair.create_from_uri("//Alice")
            call = self.substrate.compose_call(
                call_module='Balances',
                call_function='transfer',
                call_params={
                'dest': addr,
                'value': 10000 * CHAIN_DEC
            })
            
            extrinsic = self.substrate.create_signed_extrinsic(
                        call=call,
                        keypair=keypair,
                        era={'period': 1000})

            reply = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True, wait_for_finalization=False)
            return True
        except Exception as e:
            print("Balance transfer error", e)
            return False

    #Get user's balance
    def get_balance(self, addr):

        print("get_balance of", addr)
        balance = 0
        self.substrate = self.substrate_connect()
        try:

            account_info = self.substrate.query(
                module='System',
                storage_function='Account',
                params=[addr]
            )
            print("account_info", account_info)
            balance = account_info.value['data']['free']
        except Exception as e:
            print("Retrieving balance error", str(e))

        return balance

    #Send balance
    def send_balance(self, addr, value):

        ret_dic = {}
        try:
            value = float(value)
        except:
            ret_dic["error"] = "Wrong value: {}".format(value)
            return ret_dic

        try:
            #keypair = Keypair.create_from_uri("//Alice")
            self.substrate = self.substrate_connect()
            call = self.substrate.compose_call(
                call_module='Balances',
                call_function='transfer',
                call_params={
                'dest': addr,
                'value': value * CHAIN_DEC
            })
            
            extrinsic = self.substrate.create_signed_extrinsic(
                        call=call,
                        keypair=self.keypair,
                        era={'period': 64})

            reply = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True, wait_for_finalization=False)
            extrinsic_hash = str(reply['extrinsic_hash'])
            ret_dic["success"] = "Balance of {} SPDR Transferred to {}".format(value, addr)
            ret_dic["block_hash"] = extrinsic_hash
            return ret_dic
        except Exception as e:
            ret_dic["error"] = "Balance transfer error: {}".format(str(e))
            return ret_dic

        ret_dic["error"] = "Something went wrong while transferring the balance" 
        return ret_dic

    #Create wallet
    def create_wallet(self):
            
        mnemonic = Keypair.generate_mnemonic()
        n_keypair = None
        try:
            n_keypair = Keypair.create_from_mnemonic(mnemonic)
        except:
            return None
        
        self.keypair = n_keypair
        return n_keypair

    #Import exisiting wallet by seed phrase
    def import_wallet(self, mnemonic):

        #Clean whitespaces in the mnemonic and ensure it's a 12-word
        mnemonic = str(mnemonic)
        mnemonic = re.sub(' +', ' ', mnemonic)
        mnemonic = mnemonic.strip()
        if len(mnemonic.split()) != 12:
            return None

        n_keypair = None
        try:
            n_keypair = Keypair.create_from_mnemonic(mnemonic)
        except:
            return None

        self.keypair = n_keypair
        return n_keypair

    #Parses proposals with Input in Json format
    def parse_dict_args(self, darg):

        #Check the module name is correct and available for voting on the Testnet (set in spiderdao_env BOT_MODULES env var)
        module_name = darg["module_name"]
        if module_name not in chain_modules:
            print("Module not found")
            return {"error" : "Module not found"}

        #Check the function name is correct and related to the called Module above
        call_id = darg["call_id"]
        if call_id not in chain_modules[module_name]:
            print("Call not found")
            return {"error" : "call_id not found"}

        #Verify passed call parameters
        params = darg["call_params"]
        i = 2
        #[{'name': 'dest', 'type': 'LookupSource'}, {'name': 'value', 'type': 'Compact<Balance>'}]
        print("CLIENT PARAMS", params)
        for ar in chain_modules[module_name][call_id]["args"]:
            if ar["name"] not in params:
                return {"error" : "call_params error"}

            name = ar["name"]
            val = params[name]
            if "balance" in ar["type"].lower():
                val = float(val) * CHAIN_DEC

            params[name] = val
            i = i + 1

        print("DAO PARAMS", params)

        d_args = {}
        d_args["module_name"] = module_name
        d_args["call_id"] = call_id
        d_args["params"] = params

        return d_args

    #Parses proposals with Input in text format (from the Bot or propose_example.py)
    def parse_args(self, args):

        #RECHECK
        if isinstance(args, str):
            args = args.split()

        #Check the module name is correct and available for voting on the Testnet (set in spiderdao_env BOT_MODULES env var)
        module_name = args[0]
        if module_name not in chain_modules:
            print("Module not found")
            return {"error" : f"Module not found {module_name}"}

        #Check the function name is correct and related to the called Module above
        call_id = args[1]
        if call_id not in chain_modules[module_name]:
            print("Call not found")
            return {"error" : f"call_id not found {call_id}"}
        
        if (len(args) - 2) != len(chain_modules[module_name][call_id]["args"]):
            print("Wrong args")
            return {"error" : "call_params error"}
        
        params = {}
        i = 2
        #Verify passed call parameters
        #mapping between Discord requests and chain modules calls
        for ar in chain_modules[module_name][call_id]["args"]:
            name = ar["name"]
            val = args[i]
            if "balance" in ar["type"].lower():
                val = float(val) * CHAIN_DEC

            params[name] = val
            i = i + 1

        d_args = {}
        d_args["module_name"] = module_name
        d_args["call_id"] = call_id
        d_args["params"] = params

        return d_args

    #Create a call from proposal parameters
    def create_substrate_call(self, call_params):

        self.substrate = self.substrate_connect()
        call = self.substrate.compose_call(
            call_module=call_params["module_name"],
            call_function=call_params["call_id"],
            call_params=call_params["params"]
        )

        call_ascii = str(call)
        encoded_proposal = str(call.data)
        print("call", call_ascii)
        print("encoded_proposal", encoded_proposal)

        return call, call_ascii, encoded_proposal

    #Execute the call
    #Waits for Block inclusion and finalization
    def submit_extrinsic(self, call):

        #keypair = Keypair.create_from_mnemonic(bot_users[ctx.author]["keypair"].mnemonic)
        self.substrate = self.substrate_connect()
        wallet_info = f" \
        Seed phrase: `{ self.keypair.mnemonic}`\n \
        Address: `{ self.keypair.ss58_address}`\n \
        Public Key: `{ self.keypair.public_key}`\n \
        Private key: `{ self.keypair.private_key}`\n"
        #print(f"Keypair:\n{wallet_info}")

        extrinsic = self.substrate.create_signed_extrinsic(
                    call=call,
                    keypair=self.keypair,
                    era={'period': 64})
        
        reply = {}
        try:
            reply = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True, wait_for_finalization=self.wait_for_finalization) #wait_for_inclusion
        except Exception as e:
            print("Network Error", f"Call: {call}", e)
            reply = {}
            reply["error"] = str(e)
            return reply

        return reply["block_hash"]

    #Get proposal index from supplied list of events `lev`
    def get_PropIndex(self, lev):

        PropIndex = None
        for ev in lev:
            if ev.event_index == "1e00":
                for p in ev.params:
                    if p["type"] == "PropIndex":
                        PropIndex = p["value"]
                        break

        return PropIndex

    #Submit preimage hash and pay storage fees
    def note_preimage(self, encoded_proposal):

        self.substrate = self.substrate_connect()
        call = self.substrate.compose_call(
                call_module='Democracy',
                call_function='note_preimage',
                call_params={
                'encoded_proposal': encoded_proposal
            }
        )

        block_hash = self.submit_extrinsic(call)
        if "error" in block_hash:
            return block_hash

        #print("NOTE PREIMAGE", str(block_hash))
        return block_hash

    #Prepare proposal before submitting
    def pre_propose(self, arg, json=False):

        print("ARG", arg)

        self.substrate = self.substrate_connect()
        
        call_params = None
        if json:
            call_params = self.parse_dict_args(arg)
        else:
            call_params = self.parse_args(arg)

        if "error" in call_params:
            return call_params

        #print("ARG", arg, call_params)
        call, call_ascii, encoded_proposal = self.create_substrate_call(call_params)

        self.encoded_proposal = encoded_proposal
        self.call_ascii = call_ascii
        block_hash = None
        ev_bh = None

        block_hash = self.note_preimage(encoded_proposal)
        if "error" in block_hash:
            return block_hash

        ev_bh = self.substrate.get_events(block_hash=block_hash)

        preimage_hash = ""
        storageFee = -1

        lev = list(ev_bh)
        for ev in lev:
            if ev.event_index == "1e0b": #'event_id': 'PreimageNoted'
                pl = list(ev.params)
                for p in pl:
                    if p["type"] == "Hash":
                        preimage_hash = p["value"]
                    if p["type"] == "Balance":
                        storageFee = p["value"] / CHAIN_DEC
                        
        if preimage_hash == "" or storageFee < 0:
            err_dic = {"error" : "duplicate proposal"}
            return err_dic

        proposal = {}
        proposal["preimage_hash"] = str(preimage_hash)
        proposal["storageFee"] = storageFee
        proposal["call"] = call_ascii
        proposal["block_hash"] = block_hash
        #proposal["result"] = lev

        return proposal

    #Actual Propose transaction
    def propose(self, preimage_hash):

        #lock.acquire()
        self.substrate = self.substrate_connect()
        call = self.substrate.compose_call(
                call_module='Democracy',
                call_function='propose',
                call_params={
                'proposal_hash': preimage_hash,
                'value' : 100 * CHAIN_DEC
            }
        )

        block_hash = self.submit_extrinsic(call)
        if "error" in block_hash:
            return block_hash

        ev = self.substrate.get_events(block_hash=block_hash)

        PropIndex = str(self.get_PropIndex(ev))

        proposal = {}
        proposal["preimage_hash"] = preimage_hash
        proposal["block_hash"] = block_hash
        proposal["PropIndex"] = PropIndex
        proposal["launch_period"] = launch_period

        prop_dec = self.get_proposal_info(preimage_hash)
        if prop_dec is None:
            print("prop_dec is None")
            prop_dec = {}
            prop_dec["proposal"] = self.call_ascii
            prop_dec["encoded_proposal"] = None

        #DELTRECH
        prop_info = {
            "proposer_addr" : self.keypair.ss58_address,
            "proposer_discord_username" : "",
            "proposer" : self.keypair.public_key,
            "preimage_hash" : preimage_hash,
            "proposal" : prop_dec["proposal"],
            "prop_idx" : PropIndex,
            "ref_idx" : PropIndex
            #"encoded_proposal" : prop_dec["encoded_proposal"]
        }
        proposal["prop_info"] = prop_info
        #proposal_dict[PropIndex] = prop_info

        # #Store proposal data in DB
        
        # print("DB INS", PropIndex, prop_info)
        # self.proposals_db.set(PropIndex, prop_info)
        # self.proposals_db.dump()
        # lock.release()

        return proposal

    #Second a proposal
    def second(self, prop_idx):

        props = self.get_props()
        print("SECOND", props)
        if prop_idx not in props["proposals_idx"]:
            error_dict = {}
            error_dict["error"] = f"{prop_idx} Wrong proposal"
            return error_dict

        prop_idx = int(prop_idx)
        self.substrate = self.substrate_connect()
        call = self.substrate.compose_call(
                call_module='Democracy',
                call_function='second',
                call_params={
                    'proposal': prop_idx,
                    'seconds_upper_bound' : 6,
            }
        )

        block_hash = self.submit_extrinsic(call)
        if "error" in block_hash:
            return block_hash

        return block_hash

    #Vote on a Referendum
    def vote(self, ref_index, vote_value):

        self.substrate = self.substrate_connect()

        ref_status = self.get_ref_info(ref_index)
        if ref_status["status"] != "Ongoing":
            err_dic = {}
            err_dic["error"] = "Referendum not found"
            return err_dic
            
        _vote = {}
        if vote_value == "yes":
            #128 as shown in https://github.com/polkascan/py-scale-codec/blob/0f0943fe1aebab9ff16e9e664444ae02fa75894a/test/test_extrinsic_payload.py#L708
            _vote = 128 
        elif vote_value == "no":
            _vote = 0
        else:
            return {"error": f"Unrecognized vote {_vote}"}

        call = self.substrate.compose_call(
                call_module='Democracy',
                call_function='vote',
                call_params = {
                    'ref_index': int(ref_index),
                    'vote': {
                                "Standard" : {
                                    "vote": _vote,
                                    "balance": 100 * CHAIN_DEC,
                                }
                            }
                }
        )
        
        #self.wait_for_finalization = True
        block_hash = self.submit_extrinsic(call)
        #self.wait_for_finalization = False
        if "error" in block_hash:
            return block_hash
        vote_ret = {}
        vote_ret["block_hash"] = block_hash
        vote_ret["vote"] = vote_value
        vote_ret["ref_index"] = ref_index

        return vote_ret

    #Get a Referendum data from chain metadata, map it with the Referendum in DB and return data in Json format
    def get_ref_info(self, ref_index):

        #self.substrate = self.substrate_connect()

        rref = None
        dref = {}

        try:
            self.substrate = self.substrate_connect()

            rref = self.substrate.query(
                module='Democracy',
                storage_function='ReferendumInfoOf',
                params=[int(ref_index)]
            )
        except:
            if rref is None:
                dref["status"] = "Referendum not found"
                return dref

        #check
        const_deposit = 100 * 10**11 
        t_const_deposit = 100 * 10**12

        rref = ast.literal_eval(str(rref))

        if rref is None:
            dref["status"] = "Referendum not found"

        elif 'Ongoing' in rref:
            ref = rref["Ongoing"]
            dref["status"] = "Ongoing"
            dref["end_block"] = ref["end"]
            dref["proposal"] = ref["proposalHash"]
            dref["ayes"] = int(ref["tally"]["ayes"] / const_deposit)
            dref["nays"] = int(ref["tally"]["nays"] / const_deposit)
            dref["total_votes"] = int(ref["tally"]["turnout"] / t_const_deposit)

        elif 'Finished' in rref:
            dref["status"] = "Finished"
            ref = rref["Finished"]
            dref["approved"] = "yes" if ref["approved"] else "no"
            dref["end_block"] = ref["end"]

        return dref

    #Get proposal info from proposal_hash in simple format
    def get_proposal_info(self, proposal_hash):

        self.substrate = self.substrate_connect()
        preimage = self.substrate.query(
            module='Democracy',
            storage_function='Preimages',
            params=[proposal_hash]
        )

        if preimage is None:
            return None

#{'Available': {'data': '0x040000d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d0b00d07e92ffc8', 'provider': '0x2cbbf564af905306ddc9ae9442589e155357f96dfb138490241ddcccc7a7f06a', 'deposit': 420000000000, 'since': 45498, 'expiry': None}}

#{'call_index': '0x0400', 'call_function': 'transfer', 'call_module': 'Balances', 'call_args': [{'name': 'dest', 'type': 'LookupSource', 'value': '0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d'}, {'name': 'value', 'type': 'Compact<Balance>', 'value': 221000000000000}], 'call_hash': '0x9fcc7063b2d6b27b3fce06dd19bbb42b3f7a9152595efbf95dc3a8e57a67887b'}

        d_preimage = ast.literal_eval(str(preimage))
        print("d_preimage", d_preimage)
        if "Available" not in d_preimage:
            return None

        ret_d = None
        try:
            #encoded_proposal = str(d_preimage["Available"]["data"])
            call = self.substrate.decode_scale('Call', d_preimage["Available"]["data"])

            call = ast.literal_eval(str(call))
            
            module_name = call["call_module"]
            call_id = call["call_function"]
            params = call["call_args"]
            params_str = ""

            for p in params:
                    #return {"error" : "Preimage decoding call_params error"}
                name = p["name"]
                val = p["value"]

                try:
                    val = self.substrate.ss58_encode(val)
                except:
                    val = p["value"]

                if "balance" in p["type"].lower():
                    val = float(val) / CHAIN_DEC
                    
                params_str = params_str + f"{name}:{str(val)} "

                
            ret_d = {}
            ret_d["module_name"] = module_name
            ret_d["call_id"] = call_id
            ret_d["params"] = params
            ret_d["proposal"] = f"Module: {module_name}\n🧮 Module function: {call_id}\n⌨️ Function parameters: {params_str}"
            ret_d["proposer"] = d_preimage["Available"]["provider"]
            ret_d["proposer_addr"] = Keypair(public_key=str(d_preimage["Available"]["provider"]), ss58_format=42).ss58_address
            ret_d["deposit"] = float(d_preimage["Available"]["deposit"])/ CHAIN_DEC
            #ret_d["encoded_proposal"] = encoded_proposal
# 📇 Proposal Index 30
# 👤 Proposed by: 5HMpBMX8PGwNpzo3XAwD1FcqiB69XJhdbhJyt7ZyvgLeF7Am
# 🧩 Proposal Module: Balances
# 🧮 Module function: transfer
# ⌨️ Function parameters: dest:5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY
# 🔢 Value:59.0

        except Exception as e:
            print("Error decoding proposal hash", str(e))

        return ret_d

    #Return last block number and hash from the chain
    def get_last_block(self):
        
        last_block_hash = None
        last_block_number = None

        try:
            last_block_hash = self.substrate.get_chain_head()
            last_block_number = self.substrate.get_block_number(last_block_hash)
        except:
            last_block_number = g_last_block_number
        #get_block_metadata(self, block_hash=None, decode=True):
        return last_block_hash, last_block_number

    #Parse Referendum data into UI friendly format
    def get_ref_status(self, ref_idx, props=None):
        """
            props: default argument is passed as None in case get_ref_status is called in a loop i.e From get_all_refs() the props arg will be passed one time
            instead of calling get_props() in each iteration
        """

        ref = self.get_ref_info(ref_idx)
        #print("get_ref_status ref", ref, ref_idx)
        ref_msg = f"🎗 Referendum `{ref_idx}` "
        end_str = ""
        status = ""
        tally = ""
        
        #{'status': 'Finished', 'approved': 'no', 'end_block': 27250}
        #{'status': 'Ongoing', 'end_block': 23300, 'proposal': '0x9d82789583cecb141eff0a86420cd088a0526d0cea40dc6c77e42cfe0b556e3d', 'ayes': 1, 'nays': 0, 'total_votes': 1}

        ref_json = {}


            #DELTRECH
            # prop_idx = str(p['col1'])
            # if prop_idx in d_props["proposals_idx"]:
            #     continue

            # proposal = {}
            # proposal["prop_idx"] = prop_idx
            # proposal["proposal_hash"] = p['col2']
            # proposal["proposed_by"] = p['col3']

            # d_props["proposal_hash_idx"] = {prop_idx : p['col2']}
            # d_props["proposals"].append(proposal)
            # d_props["proposals_idx"].append(prop_idx)


        prop_idx = "-1"
        preimage_hash = ""
        #If the Referendum is not ended, if ended will not show proposal hash as shown in sample output above
        if "proposal" in ref:
            preimage_hash = ref["proposal"]
            # for p in props["proposals"]:
            #     if p["proposal_hash"] == ref["proposal"]:
            #         prop_idx = p
            #         preimage_hash = p["proposal_hash"]
            #         break
        # #if prop_index not in proposal_dict:
        # if not self.proposals_db.exists(prop_idx):
        #     #ref_msg = ref_msg + " Not Found #1"
        #     #ref_json["ref_msg"] = ref_msg
        #     return None

        #prop = self.proposals_db.get(prop_idx)
        prop = None
        proposer = None
        proposal_str = None
        if "proposal" in ref:
            prop = self.get_proposal_info(preimage_hash)

            if "proposer_discord_username" in prop:
                proposer = prop["proposer_discord_username"]
            else:
                proposer = prop["proposer_addr"]

            proposal_str = prop["proposal"]

        _, last_block = self.get_last_block()
        if "status" not in ref:
            #ref_msg = ref_msg + " Not Found #2"
            #ref_json["ref_msg"] = ref_msg
            return None

        if ref["status"] == "Finished":
            #Referendum `1` has ended {X time ago}, number of voters {}, results X% Approved/Not Approved
            status = "ended"

            end_block = int(ref["end_block"])

            diff_tm = int(int(last_block) - end_block) * 6
            end_str = timeago.format(datetime.timedelta(seconds=diff_tm))

            if ref["approved"] == "yes":
                tally = "Approved"
            else:
                tally = "Not Approved"

            if prop is not None:
                ref_msg = ref_msg + f" `{tally}`, `{status}` {end_str}.\n \
                    Proposed by `{proposer}`, Proposal `{proposal_str}`"
            else:
                ref_msg = ref_msg + f" `{tally}`, `{status}` {end_str}."

            ref_json["status"] = status
            ref_json["end_str"] = end_str
            ref_json["tally"] = tally
            ref_json["ref_msg"] = ref_msg
            ref_json["proposer"] = proposer
            ref_json["proposal_str"] = proposal_str
            ref_json["ref_idx"] = str(ref_idx)
            
        elif ref["status"] == "Ongoing":
            #Referendum `1` is ongoing will end in {X time}, number of voters {}, results X% Approved/Not Approved

            status = "ongoing"
            
            end_block = int(ref["end_block"])
            diff_tm = int(end_block - int(last_block)) * 6
            date_now = datetime.datetime.now()
            now = date_now + datetime.timedelta(seconds=diff_tm)
            end_str = timeago.format(now, date_now, "en")
            
            n_voters = ref["total_votes"]
            current_perc = "0"
            if n_voters > 0:
                current_perc = int(float(int(ref["ayes"])/int(ref["total_votes"]) * 100))

            ref_msg = ref_msg + f" is `{status}` will end {end_str}, Total voters `{n_voters}`, `{current_perc}%` Approved so far.\n \
                Proposed by `{proposer}`, Proposal `{proposal_str}`"

            ref_json["status"] = status
            ref_json["end_str"] = end_str
            ref_json["voters"] = n_voters
            ref_json["ref_msg"] = ref_msg
            ref_json["proposer"] = proposer
            ref_json["proposal_str"] = proposal_str
            ref_json["ref_idx"] = str(ref_idx)
            
        else:
            ref_msg = ref_msg + " Not Found #3"
            print(ref_msg)
            ref_json = None

        return ref_json #ref_msg

    #Get all referendums in friendly format
    def get_all_refs(self):

        self.substrate = self.substrate_connect()
        refs_cnt = self.substrate.query(
            module='Democracy',
            storage_function='ReferendumCount',
            params=None
        )

        refs_cnt = int(str(refs_cnt))
        print("ReferendumCount", refs_cnt)

        if refs_cnt == 0:
            return []

        refs_list = []
        ref_th = []

        s_props = self.get_props()
        # if len(list(s_props)) == 0:
        #     return None

        #DELTRECH
        for r in range(refs_cnt,-1, -1):
            ref_json = self.get_ref_status(str(r), props=s_props)
            if ref_json is None:
                continue

            self.tmp_refs.append(ref_json)

        #self.tmp_refs = self.tmp_refs[:5]
        for ref_json in self.tmp_refs[:5]:
            refs_list.append(ref_json)

        if len(refs_list) > 0:
            return refs_list
        else:
            return []
    
    #Get all proposals
    def get_props(self):

        self.substrate = self.substrate_connect()
        props = self.substrate.query(
            module='Democracy',
            storage_function='PublicProps',
            params=None
        )

        if props is None:
            d_props["current_proposals"] = 0
            return d_props
            
        props = ast.literal_eval(str(props))
        print("Proposals", props, type(props))

        if props is None or len(props) == 0:
            d_props["current_proposals"] = 0
            return d_props

        d_props["current_proposals"] = len(props)

        d_props["proposals"] = []
        d_props["proposals_idx"] = []
        for p in props:
            prop_idx = str(p['col1'])
            if prop_idx in d_props["proposals_idx"]:
                continue

            proposal = {}
            proposal["prop_idx"] = prop_idx
            proposal["proposal_hash"] = p['col2']
            proposal["proposed_by"] = p['col3']

            #DELTRECH
            d_props["proposal_hash_idx"] = {prop_idx : p['col2']}
            d_props["proposals"].append(proposal)
            d_props["proposals_idx"].append(prop_idx)

        return d_props

    #Get a Proposal data from chain metadata, map it with the Proposal in DB and return data in Json format
    def get_proposal(self, prop_idx, props=None):
        
        prop_idx = str(prop_idx)

        if props == None:
            props = self.get_props()

        if len(list(props)) == 0:
            return None

            #DELTRECH
            # prop_idx = str(p['col1'])
            # if prop_idx in d_props["proposals_idx"]:
            #     continue

            # proposal = {}
            # proposal["prop_idx"] = prop_idx
            # proposal["proposal_hash"] = p['col2']
            # proposal["proposed_by"] = p['col3']

            # d_props["proposal_hash_idx"] = {prop_idx : p['col2']}
            # d_props["proposals"].append(proposal)
            # d_props["proposals_idx"].append(prop_idx)

        preimage_hash = ""

        if prop_idx in props["proposals_idx"]:

            """
            Extract preimage_hash from proposals dictionary
            """
            for p in props["proposals"]:
                if prop_idx == p["prop_idx"]:
                    preimage_hash = p["proposal_hash"]
                    break
        else:
            print(f"Proposal {prop_idx} doesn't exist")
            return None

        prop = self.get_proposal_info(preimage_hash)
        proposer = ""
        if "proposer_discord_username" in prop:
            proposer = prop["proposer_discord_username"]
        else:
            proposer = prop["proposer_addr"]
            
        proposal_str = prop["proposal"]

        # if not self.proposals_db.exists(prop_idx):
        #     print(f"Proposal {prop_idx} doesn't exist in DB")
        #     return None

        # prop = self.proposals_db.get(prop_idx)
        # proposer = prop["proposer_addr"] if prop["proposer_discord_username"] == "" else prop["proposer_discord_username"]
        # proposal_str = prop["proposal"]
        prop_msg = f"\
📇 Proposal Index {prop_idx}\n \
👤 Proposed by: {proposer}\n \
🧩 Proposal {proposal_str}\n"

        prop_json = {}
        prop_json["prop_idx"] = prop_idx
        prop_json["proposer"] = proposer
        prop_json["proposal_str"] = proposal_str
        prop_json["prop_msg"] = prop_msg

        return prop_json

    def get_all_proposals(self):

        props = self.get_props()
        if props["current_proposals"] == 0:
            return []

        proposals_list = []
        # s_props = self.proposals_db.getall()
        # if len(list(s_props)) == 0:
        #     return []

        # print("s_props", s_props)
        for prop_idx in props["proposals_idx"]: 
        
            prop_msg = self.get_proposal(prop_idx, props=props)
            if prop_msg is None:
                continue

            proposals_list.append(prop_msg)

        if len(proposals_list) > 0:
            return proposals_list
        else:
            return []

    #If proposal originated from Discord bot user, username is stored in DB here
    def db_set_user(self, PropIndex, username):

        #DELTRECH
        # prop = self.proposals_db.get(PropIndex)
        # prop["proposer_discord_username"] = username
        # self.proposals_db.set(PropIndex, prop)
        
        return

    #Helper function to parse chain events `Started`
    def parse_referendum_started(self, ledx):

        ref_dic = {}
        for e in ledx:
            if e.event_index == "1e01": #Tabled
                for ep in list(e.params):
                    if ep["type"] == "PropIndex":
                        ref_dic["PropIndex"] = str(ep["value"])

                    if ep["type"] == "Vec<AccountId>":
                        ref_dic["pub_key"] = str(ep["value"][0])

            if e.event_index == "1e03": #Started
                for ep in list(e.params):
                    if ep["type"] == "ReferendumIndex":
                        ref_dic["ReferendumIndex"] = str(ep["value"])

                    if ep["type"] == "VoteThreshold":
                        ref_dic["VoteThreshold"] = str(ep["value"])

        # if ref_dic["PropIndex"] != ref_dic["ReferendumIndex"]:
        #     prop = self.proposals_db.get(ref_dic["PropIndex"])
        #     prop["ref_idx"] = ref_dic["ReferendumIndex"]
        #     self.proposals_db.set(ref_dic["PropIndex"], prop)
        #     print("PropIndex -> ReferendumIndex", ref_dic["PropIndex"], ref_dic["ReferendumIndex"])
            
        ref_dic["user"] = ref_dic["pub_key"]

        return ref_dic

    #Helper function, a callback called when `Started` event occurs (for users notification)
    async def send_referendum_started(self, ledx, ebh):

        dex = self.parse_referendum_started(ledx)
        
        ReferendumIndex = str(dex["ReferendumIndex"])
        PropIndex = dex["PropIndex"]
        user = dex["user"]
        msg_rep = f"Referendum `{ReferendumIndex}` Started from Proposal `{PropIndex}` by `{user}` \n \
            To Vote call: !vote `{ReferendumIndex}` [yes|no]"

        return msg_rep, dex

    #Helper function to parse chain events `Passed` or `NotPassed`
    def parse_referendum_result(self, ledx):

        ref_dic = {}
        for e in ledx:
            if e.event_index == "1e04": #Tabled
                for ep in list(e.params):
                    if ep["type"] == "ReferendumIndex":
                        ref_dic["ReferendumIndex"] = str(ep["value"])
                        ref_dic["result"] = "Approved"

            if e.event_index == "1e05": #Started
                for ep in list(e.params):
                    if ep["type"] == "ReferendumIndex":
                        ref_dic["ReferendumIndex"] = str(ep["value"])
                        ref_dic["result"] = "Not Approved"

        return ref_dic

    #Helper function, a callback called when `Passed` or `NotPassed` event occurs (for users notification)
    async def show_referendum_result(self, ledx, ebh):

        dex = self.parse_referendum_result(ledx)
        ReferendumIndex = str(dex["ReferendumIndex"])
        result = dex["result"]
        msg_rep = f"Referendum `{ReferendumIndex}` Result `{result}`"

        return msg_rep, dex

class SpiderDaoChain:
    """
    SpiderDAO Chain Listener Interface
    - Listens to chain events
    - Send observed events to passed callback `chain_events_cb`
    """

    def __init__(self, node_url=None, chain_events_cb=None):

        if node_url is None:
            self.node_url = NODE_URL
        else:
            self.node_url = node_url

        self.substrate = self.substrate_connect()

        #self.run_chain_event_loop(chain_events_cb)

        self.chain_listen_thread = threading.Thread(target=self.run_chain_event_loop, args=(chain_events_cb,))
        self.chain_listen_thread.start()

        return

    def run_chain_event_loop(self, chain_events_cb):
        asyncio.run(self.get_chain_head(chain_events_cb))
        return

    def substrate_connect(self):
        self.substrate = SubstrateInterface(
                    url=self.node_url,
                    ss58_format=42,
                    type_registry_preset='westend',
        )

        #self.substrate.update_type_registry_presets()
        return self.substrate

    async def event_process(self, lev, ebh, cb_ch):
        
        for ev in lev:
            await cb_ch(ev.event_index, lev, ebh)

        return

    #Chain events listener
    async def get_chain_head(self, cb_ch):
        while True:
            try:
                ebh = self.substrate.get_chain_head()
                if ebh is None:
                    await asyncio.sleep(4)
                    continue

                ebh = str(ebh)
                #print("LATEST BLOCK HASH", ebh)
                g_last_block_number = self.substrate.get_block_number(ebh)
                ev = self.substrate.get_events(block_hash=ebh)
                await self.event_process(ev, ebh, cb_ch)

            except Exception as e: 
                print(e)
                pass
            
            await asyncio.sleep(4)
