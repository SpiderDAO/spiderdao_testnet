import ast
import base64
from datetime import datetime
import datetime
from substrateinterface import Keypair
import json
from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, send_from_directory)
from flask_cors import CORS
from cerberus import Validator
import sys

sys.path.insert(0, '../src')
from spiderdao import *

app = Flask(__name__)
CORS(app)

error_dict = {"error" : "something is wrong"}
nusers = {}
CHAIN_DEC = 10**12

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return {"error" : "route not found"}, 404

"""
/create_wallet
/import_wallet
/pre_propose
/propose
/second
/vote
/get_ref
/get_balance
/get_chain_head
/get_prop
"""

def check_auth(jso):

    spdr = None
    err_msg = ""
    errors_dict = {
        "auth_err" : "User not authorized. Create/Import wallet first",
        "network_err" : "Something wrong"
    }
    
    if jso["spider_id"] in nusers:
        pub_addr = nusers[jso["spider_id"]]

        try:
            spdr = SpiderDaoInterface(mnemonic=jso["phrase"])
            if spdr.keypair.ss58_address != pub_addr:
                err_msg = errors_dict["auth_err"]
                return None, err_msg
        except Exception as e:
            err_msg = errors_dict["network_err"]
            print("Error Creating SpiderDaoInterface", e)
    else:
        err_msg = errors_dict["network_err"]

    return spdr, err_msg

create_wallet_schema = {
    'spider_id': {
        'type': 'string', 'required': True
    },
    'request_id': {
        'type': 'string', 
        'required': False
    }
}

@app.route('/create_wallet', methods = ['POST', 'GET'])
def create_wallet():
    req = {
        "auth" : "xxxx"
    }

    jso = {}
    if request.method == 'POST':
        jso = request.json
        v = Validator(create_wallet_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["create_wallet"] = create_wallet_schema
            return error_dict

        spdr = SpiderDaoInterface()
        n_keypair = spdr.create_wallet()

        current_balance = spdr.get_balance(n_keypair.ss58_address)
        if current_balance == 0:
            if not spdr.set_balance(n_keypair.ss58_address):
                reason = f"Error transferring initial balance to `{n_keypair.ss58_address}`"
                print(reason)
                error_dict["reason"] = reason
                return jsonify(error_dict)

        balance = spdr.get_balance(n_keypair.ss58_address)
        balance = str(round(float(balance / CHAIN_DEC), 4))

        #wallet
        wallet = {
            "status" : "created",
            "mnemonic" : n_keypair.mnemonic,
            "address" : n_keypair.ss58_address,
            "public_key" : n_keypair.public_key,
            "private_key" : n_keypair.private_key,
            "balance" : balance #RECHECK
        }

        nusers[jso["spider_id"]] = n_keypair.ss58_address
        return jsonify(wallet)
    
    return jsonify(error_dict)

import_wallet_schema = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': True
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

@app.route('/import_wallet', methods = ['POST', 'GET'])
def import_wallet():

    req = {
        "auth" : "xxxx",
        "phrase" : "phrase phrase x12"
    }

    jso = {}
    if request.method == 'POST':
        jso = request.json
        
        v = Validator(import_wallet_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["import_wallet"] = import_wallet_schema
            return error_dict

        spdr = SpiderDaoInterface()
        n_keypair = spdr.import_wallet(jso["phrase"])
        if n_keypair is None:
            error_dict["reason"] = "keypair is not valid"

        current_balance = spdr.get_balance(n_keypair.ss58_address)
        if current_balance == 0:
            if not spdr.set_balance(n_keypair.ss58_address):
                reason = f"Error transferring initial balance to `{n_keypair.ss58_address}`"
                print(reason)
                error_dict["reason"] = reason
                return jsonify(error_dict)

        balance = spdr.get_balance(n_keypair.ss58_address)
        balance = str(round(float(balance / CHAIN_DEC), 4))

        wallet = {
            "status" : "imported",
            "mnemonic" : n_keypair.mnemonic,
            "address" : n_keypair.ss58_address,
            "public_key" : n_keypair.public_key,
            "private_key" : n_keypair.private_key,
            "balance" : balance #RECHECK
        }
        
        nusers[jso["spider_id"]] = n_keypair.ss58_address
        return jsonify(wallet)
    
    return jsonify(error_dict)

pre_propose_schema = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': True
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    },
    'module_name':
    {
        'type': 'string', 
        'required': True
    },
    'call_id':
    {
        'type': 'string', 
        'required': True
    },
    'call_params':
    {
        'type': 'dict', 
        'required': False
    },
}

@app.route('/pre_propose', methods = ['POST', 'GET'])
def pre_propose():

#prop = "Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 58"
    req = {

        "spider_id" : "xxxx",
        "module_name" : "Balances",
        "call_id" : "transfer",
        "call_params" : {
            "dest" : "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "value" : 58
        }
    }

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(pre_propose_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["pre_propose"] = pre_propose_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict
            
        proposal = spdr.pre_propose(jso, json=True)
        if "error" in proposal:
            return jsonify(proposal)
        #ret
        #proposal["preimage_hash"] = str(preimage_hash)
        #proposal["storageFee"] = storageFee
        #proposal["call"] = call_ascii
        #proposal["block_hash"] = block_hash
        #proposal["result"] = ev_bh

        return jsonify(proposal)
    
    return jsonify(error_dict)

propose_schema = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'preimage_hash':
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': True
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

@app.route('/propose', methods = ['POST', 'GET'])
def propose():

#prop = "Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 58"

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(propose_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["propose"] = propose_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict

        proposal = spdr.propose(jso["preimage_hash"])
        if "error" in proposal:
            return jsonify(proposal)

        #proposal["block_hash"] = block_hash
        #proposal["PropIndex"] = self.get_PropIndex(ev)
        #proposal["launch_period"] = launch_period
        return jsonify(proposal)
    
    return jsonify(error_dict)

second_schema = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'prop_index':
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': True
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    },
}

@app.route('/second', methods = ['POST', 'GET'])
def second():

#prop = "Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 58"
    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(second_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["second"] = second_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict

        block_hash = spdr.second(jso["prop_index"])
        if "error" in block_hash:
            error_dict["reason"] = block_hash["error"]
            return jsonify(error_dict)

        second = {}
        second["block_hash"] = block_hash

        return jsonify(second)
    
    return jsonify(error_dict)


vote_schema = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'ref_index':
    {
        'type': 'string', 
        'required': True
    },
    'vote':
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': True
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

@app.route('/vote', methods = ['POST', 'GET'])
def vote():

    if request.method == 'POST':
        jso = request.json

        v = Validator(vote_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["vote"] = vote_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict
        
        try:
            vote = spdr.vote(jso["ref_index"], jso["vote"])
            return jsonify(vote)
        except:
            return jsonify(error_dict)
        #vote_ret["block_hash"] = block_hash
        #vote_ret["vote"] = vote_value
        #vote_ret["ref_index"] = ref_index
        
        return jsonify(vote)
    
    return jsonify(error_dict)


get_ref_schema  = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'ref_index':
    {
        'type': 'string', 
        'required': False
    },
    'phrase':
    {
        'type': 'string', 
        'required': False
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

#Returns a list of Available Referendums
@app.route('/get_ref', methods = ['POST', 'GET'])
def get_ref():

    if request.method == 'POST':
        jso = request.json

        v = Validator(get_ref_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_ref"] = get_ref_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict

        ref_list = []
        if "ref_index" in jso and int(jso["ref_index"]) >= 0:
            ref = spdr.get_ref_status(jso["ref_index"])
            ref_list.append(ref)
        else:
            ref_list = spdr.get_all_refs()

        if len(ref_list) == 0:
            ref_err = ["No Referendums Available"]
            return jsonify(ref_err)
        
        return jsonify(ref_list)

    return jsonify(error_dict)

get_balance_schema  = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'address':
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': False
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

@app.route('/get_balance', methods = ['POST', 'GET'])
def get_balance():

    if request.method == 'POST':
        jso = request.json

        v = Validator(get_balance_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_balance"] = get_balance_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict

        balance = spdr.get_balance(jso["address"])
        if balance is None:
            return jsonify(error_dict)

        #ref
        balance_ret = {
            "balance" : balance,
            "address" : jso["address"]
        }
        
        return jsonify(balance_ret)
    
    return jsonify(error_dict)

get_props_schema  = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': False
    },
    'prop_index':
    {
        'type': 'string', 
        'required': False
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

#Returns a list of Available Proposals
@app.route('/get_props', methods = ['POST', 'GET'])
def get_props():

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(get_props_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_props"] = get_props_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict

        prop_list = []
        if "prop_index" in jso and int(jso["prop_index"]) >= 0:
            prop = spdr.get_proposal(jso["prop_index"])
            prop_list.append(prop)
        else:
            prop_list = spdr.get_all_proposals()

        if len(prop_list) == 0:
            prop_err = ["No Proposals Available"]
            return jsonify(prop_err)

        return jsonify(prop_list)
    
    return jsonify(error_dict)

get_chain_modules_schema  = {
    'spider_id': 
    {
        'type': 'string', 
        'required': True
    },
    'phrase':
    {
        'type': 'string', 
        'required': False
    },
    'request_id':
    {
        'type': 'string', 
        'required': False
    }
}

@app.route('/get_chain_modules', methods = ['POST', 'GET'])
def get_chain_modules():

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(get_chain_modules_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_chain_modules"] = get_chain_modules_schema
            return error_dict

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return error_dict
            
        chain_modules = chain_modules
        
        return jsonify(chain_modules)
    
    return jsonify(error_dict)


if __name__ == '__main__':

    app.run(host="127.0.0.1", port='55551', debug=False, threaded=True)
    print("SpiderDAO API start")

#TODO
"""
- get_chain_head
"""

