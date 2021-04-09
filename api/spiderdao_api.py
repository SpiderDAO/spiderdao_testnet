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

#Import spiderdao
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
/get_props
"""

#Checks the user is actual Spider Router user and authorize to use the testnet
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
            if spdr.keypair is None:
                err_msg = errors_dict["auth_err"]
                return None, err_msg
                
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

    """
    /create_wallet
    description: Creates a wallet, basically "sign-up/login" for Router users

    Request payload
    {'request_id': 'create_wallet', 'spider_id': 'xxxx'}

    Response
    {
        'address': '5HeJbfgadXGstiMXj6un5CkdQSacr1EFkExDBdWQortT9xyj', 
        'balance': '10000.0', 
        'mnemonic': '...', 
        'private_key': '...', 
        'public_key': '0xf6cd37284e1f2f488d303b7c7f291cf3321b18653f922fe84f1a0696d657f057', 
        'status': 'created'
    }
    
    mnemonic: Used to import wallet in /import_wallet and other requests payload to authenticate network transactions
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json
        v = Validator(create_wallet_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["create_wallet"] = create_wallet_schema
            return jsonify(error_dict)

        spdr = SpiderDaoInterface()
        n_keypair = spdr.create_wallet()

        current_balance = spdr.get_balance(n_keypair.ss58_address)
        if current_balance == 0:
            if not spdr.set_balance(n_keypair.ss58_address):
                reason = f"Error transferring initial balance to `{n_keypair.ss58_address}`"
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
            "balance" : balance
        }

        #Adds the wallet to authenticated users
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

    """
    /import_wallet
    description: Imports a wallet, basically "login" for Router users

    Request payload
    {
        'request_id': 'create_wallet', 
        'spider_id': 'xxxx',
        'phrase' : '...',
    }

    phrase: the mnemonic that was generated
    Response
    {
        'address': '5HeJbfgadXGstiMXj6un5CkdQSacr1EFkExDBdWQortT9xyj', 
        'balance': '10000.0', 
        'mnemonic': '...', 
        'private_key': '...', 
        'public_key': '0xf6cd37284e1f2f488d303b7c7f291cf3321b18653f922fe84f1a0696d657f057', 
        'status': 'imported'
    }
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json
        
        v = Validator(import_wallet_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["import_wallet"] = import_wallet_schema
            return jsonify(error_dict)

        spdr = SpiderDaoInterface()
        n_keypair = spdr.import_wallet(jso["phrase"])
        if n_keypair == None:
            error_dict["reason"] = "keypair is not valid"
            return jsonify(error_dict)

        current_balance = spdr.get_balance(n_keypair.ss58_address)
        if current_balance == 0:
            if not spdr.set_balance(n_keypair.ss58_address):
                reason = f"Error transferring initial balance to `{n_keypair.ss58_address}`"
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
            "balance" : balance
        }
        
        #Adds the wallet to authenticated users
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

    """
    /pre_propose
    description: prepares the proposals and confirms with the users before submitting the proposal

    Request payload
    {
        'spider_id' : 'xxxx',
        'module_name' : 'Balances',
        'call_id' : 'transfer',
        'call_params' : {
            'dest' : '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY',
            'value' : 58
    }

    Response
    {
        'block_hash': '0x7efce0295cb0411580b0cac3133d94a6ba41ae2e56fb28f5a626052715ac9c18', 
        'call': "{
            'call_module': 'Balances', 
            'call_function': 
            'transfer', 
            'call_args': {
                'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 'value': 58000000000000
                }
            }", 
        'preimage_hash': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425', 
        'storageFee': 0.42
    }

    preimage_hash: used to submit the proposal in /propose
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(pre_propose_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["pre_propose"] = pre_propose_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)
            
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

    """
    /propose
    description: Submits the proposal

    Request payload
    {
        'spider_id' : 'xxxx',
        'preimage_hash' : '0x7efce0295cb0411580b0cac3133d94a6ba41ae2e56fb28f5a626052715ac9c18',
        'phrase' : '...'
    }

    Response
    {
        'PropIndex': 4, 
        'block_hash': '0xbfb7766ec80bfc61981dd594990f0171e2725e0bac2e7e92453a8e28a4327f10', 
        'launch_period': '5 minutes to be Launched', 
        'preimage_hash': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425'}
    }

    PropIndex: the proposal index generated from the chain, used to query proposal status, related referendum status, and to second a proposal in /second
    launch_period: A string to be displayed in the UI to show the Launch Period
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(propose_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["propose"] = propose_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)

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

    """
    /propose
    description: Seconds the proposal

    prop_index: is the PropIndex returned from /propose
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...',
        'prop_index' : '4'
    }

    Response
    {
        'block_hash': '0x0c943fe525dbfe24f63f03642a82a94cd0fc1bfd3218cec8038c7c5c28ee8dd2'
    }
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(second_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["second"] = second_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)

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

    """
    /vote
    description: Seconds the proposal

    vote: Vote on a Referendum either "yes" or "no"
    ref_index: the value returned from /get_ref or use PropIndex
    
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...',
        'ref_index' : '4',
        'vote': 'yes'
    }

    Response
    {
        "block_hash": "0xd2aeecd94ceb664f2b61da8fe1c79fe8d01fe03d333663119ea285b9715241ab", 
        "ref_index": 4, 
        "vote": "yes"
    }
    """

    if request.method == 'POST':
        jso = request.json

        v = Validator(vote_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["vote"] = vote_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)
        
        try:
            vote = spdr.vote(jso["ref_index"], jso["vote"])
            return jsonify(vote)
        except Exception as e:
            print("Vote Error", str(e))
            return jsonify(error_dict)
        
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

    """
    /get_ref
    description: Get a referendum or all referendums statuses if ref_index not passed
    
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...',
        'ref_index' : '4'
    }

    Response
    {
        #A list of referendums
    }
    """

    if request.method == 'POST':
        jso = request.json

        v = Validator(get_ref_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_ref"] = get_ref_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)

        ref_list = []
        ret_ref_list = []
        if "ref_index" in jso and int(jso["ref_index"]) >= 0:
            ref = spdr.get_ref_status(jso["ref_index"])
            if ref is not None:
                ret_ref_list.append(ref)
        else:
            ref_list = spdr.get_all_refs()
            for r in ref_list:
                ret_ref_list.append(r)

        ref_list = ret_ref_list

        if len(ref_list) == 0:
            ref_err = ["Referendum Not Found"]
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

    """
    /get_balance
    description: shows balance of [address]
    
    Request payload
    {
        'phrase': '...', 
        'spider_id': 'xxxx', 
        'address': '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6'
    }

    Response
    {
      "address": "5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6", 
      "balance": 9997999494026194
    }
    """

    if request.method == 'POST':
        jso = request.json

        v = Validator(get_balance_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_balance"] = get_balance_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)

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

    """
    /get_props
    description: Get a proposal info or all proposals statuses if prop_index not passed
    
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...',
        'prop_index' : '4'
    }

    Response
    {
        #A list of proposals
    }
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(get_props_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_props"] = get_props_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)

        prop_list = []
        ret_prop_list = []
        if "prop_index" in jso and int(jso["prop_index"]) >= 0:
            prop = spdr.get_proposal(jso["prop_index"])
            if prop is not None:
                prop_list.append(prop)
        else:
            prop_list = spdr.get_all_proposals()
            for p in prop_list:
                if p is not None:
                    ret_prop_list.append(p)

        prop_list = ret_prop_list
        
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

    """
    /get_chain_modules
    description: Gets chain modules and their details supported in the Testnet
    
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...'
    }

    Response
    {
        #A Json object with the chain modules and functions supported in the Testnet and their documentation
    }
    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(get_chain_modules_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["get_chain_modules"] = get_chain_modules_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)
            
        return jsonify(spdr._chain_modules)
    
    return jsonify(error_dict)


send_balance_schema  = {
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
    'address':
    {
        'type': 'string', 
        'required': True
    },
    'value':
    {
        'type': 'string', 
        'required': True
    }
}

@app.route('/send_balance', methods = ['POST', 'GET'])
def send_balance():

    """
    /send_balance
    description: Send balance to SpiderDAO user
    
    Request payload
    {
        'spider_id' : 'xxxx',
        'phrase' : '...'
        'address' : '...',
        'value' : "123"
    }

    """

    jso = {}
    if request.method == 'POST':
        jso = request.json

        v = Validator(send_balance_schema)
        valid = v.validate(jso)
        if not valid:
            error_dict["reason"] = "wrong arguments"
            error_dict["send_balance"] = send_balance_schema
            return jsonify(error_dict)

        spdr, err_msg = check_auth(jso)
        if spdr is None:
            error_dict["reason"] = err_msg
            return jsonify(error_dict)
            
        balance = spdr.send_balance(jso["address"], jso["value"])

        return jsonify(balance)
    
    return jsonify(error_dict)

if __name__ == '__main__':

    app.run(host="127.0.0.1", port='55551', debug=False, threaded=True)
    print("SpiderDAO API start")