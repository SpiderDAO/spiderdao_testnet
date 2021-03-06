import json
import requests
import time
import sys

#Sample seed phrase
#Use create_wallet to generate new phrase
phrase = 'annual isolate sea quit pelican inside whale grant during zoo glimpse issue'

data = None

#Object holds sample data for API requests
data = {
    'create_wallet' : {
        'request_id' : 'create_wallet',
        'spider_id': 'xxxx'
    },
    'import_wallet' : {
        'request_id' : 'import_wallet',
        'spider_id': 'xxxx',
        'phrase': phrase
    },
    'pre_propose' : {
        'request_id' : 'pre_propose',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'module_name' : 'Balances',
        'call_id' : 'transfer',
        'call_params' : {
            'dest' : '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY',
            'value' : 300
        }
    },
    'propose' : {
        'request_id' : 'propose',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'preimage_hash' : '0x9b8167bd60b46936a27c584dc5fa4fd47ad81e3e8c964cc67f827fc6b46db578',
    },
    'second' : {
        'request_id' : 'second',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'prop_index' : "1",
    },
    'vote' : {
        'request_id' : 'vote',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'ref_index' : "11",
        'vote' : 'yes'
    },
    'get_ref' : {
        'request_id' : 'get_ref',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'ref_index' : "11"
    },
    'get_props' : {
        'request_id' : 'get_props',
        'phrase': phrase,
        'spider_id' : 'xxxx'
    },
    'get_balance' : {
        'request_id' : 'get_balance',
        'phrase': phrase,
        'spider_id' : 'xxxx',
        'address' : '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6'
    },
    'get_chain_modules' : {
        'request_id' : 'get_chain_modules',
        'spider_id': 'xxxx',
        'phrase' : phrase
    },
    'send_balance' : {
        'request_id' : 'send_balance',
        'spider_id': 'xxxx',
        'phrase' : phrase,
        'address' : '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6',
        'value' : "123"
    }
}

# prop_index == referendum index

#Function to exit if error happens in the test
def error_check(resp):

    print("\n\n")
    if "error" in resp:
        sys.exit(0)

#Request Perform
def perform_req(req):
    url = "http://127.0.0.1:55551" #API url
    url = f"{url}/{req}"
    print("data[req]", data[req])
    r = requests.post(url, json=data[req])

    print("RAW", r.text)
    print("DAO RESPONSE", json.loads(r.text))

    return json.loads(r.text)

"""
Create a wallet:
    - should be used first time to get (mnemonic/seed phrase) and import the mnemonic to do other calls
    - In this test wallet created and imported for testing
"""

resp = perform_req("create_wallet")
print("create_wallet Resp", resp)
error_check(resp)

"""
Import a wallet:
    - Auhthorize user in the API
"""
phrase = resp["mnemonic"]
data["import_wallet"]["phrase"] = phrase
resp = perform_req("import_wallet")
print("import_wallet Resp", resp)
error_check(resp)

"""
Send Balance:
    - Send balance to other users
"""
data["send_balance"]["phrase"] = phrase
resp = perform_req("send_balance")
print("send_balance Resp", resp)
error_check(resp)

"""
Pre-propose:
    - prepare proposal and confirm submission
"""
data["pre_propose"]["phrase"] = phrase
data["pre_propose"]["call_params"]["value"] = 606 # <-- change this value for every test like make it 401, 402..etc
resp = perform_req("pre_propose")
print("pre_propose Resp", resp)
error_check(resp)

"""
Propose:
    - create actual proposal from the preimage_hash returned from pre_propose
"""
data["propose"]["phrase"] = phrase
data["propose"]["preimage_hash"] = resp["preimage_hash"]
resp = perform_req("propose")
print("propose Resp", resp)
error_check(resp)

"""
Second:
    - Seconds a proposal by prop_index (Proposal Index) returned from /propose
"""
prop_index = resp["PropIndex"]
data["second"]["phrase"] = phrase
data["second"]["prop_index"] = prop_index
resp = perform_req("second")
print("second Resp", resp)
#error_check(resp)

"""
Get Props:
    - Get the proposal that was just created in the test
"""
data["get_props"]["phrase"] = phrase
data["get_props"]["prop_index"] = prop_index
resp = perform_req("get_props")
print("get_props Resp", resp)
error_check(resp)

"""
Basic test to wait for the Referendum to be launched from the created proposal, loops exits when Referendum Starts
"""
data["get_ref"]["phrase"] = phrase
data["get_ref"]["ref_index"] = prop_index
while True:
    time.sleep(10)
    resp = perform_req("get_ref")
    print("get_ref Resp", resp)
    error_check(resp)
    resps = str(resp[0])
    print(resps)
    if "Not Found" not in resps:
        break

"""
Vote:
    - Vote on the just launched Referendum
"""
data["vote"]["phrase"] = phrase
data["vote"]["ref_index"] = prop_index
resp = perform_req("vote")
print("vote Resp", resp)
error_check(resp)

"""
Get Ref:
    - Test getting all Referendum, by passing "-1" as ref_index
"""
data["get_ref"]["phrase"] = phrase
data["get_ref"]["ref_index"] = "-1"
resp = perform_req("get_ref")
print("get_ref Resp", resp)

"""
Get Props:
    - Test getting all Proposals, by passing "-1" as prop_index
"""
data["get_props"]["phrase"] = phrase
data["get_props"]["prop_index"] = "-1"
resp = perform_req("get_props")
print("get_props Resp", resp)
error_check(resp)


"""
Get Balance:
    - Test get balance of address
"""
data["get_balance"]["phrase"] = phrase
resp = perform_req("get_balance")
print("get_balance Resp", resp)
error_check(resp)

"""
Get Chain Modules:
    - Get chain modules and their details supported by the current Testnet
"""
data["get_chain_modules"]["phrase"] = phrase
resp = perform_req("get_chain_modules")
print("get_chain Resp", resp)
error_check(resp)


"""
#Sample request payload and response for every API call

#create_wallet request
data[req] {'request_id': 'create_wallet', 'spider_id': 'xxxx'}

#create_wallet response

create_wallet Resp {'address': '5HeJbfgadXGstiMXj6un5CkdQSacr1EFkExDBdWQortT9xyj', 'balance': '10000.0', 'mnemonic': 'access toward ride leaf start bike castle best pass lobster rookie fossil', 'private_key': '0xdf7599e2d7b13d0998d62ea554c72cb79e85fd3a1371c0353e8e59c2b4fda309df7f82497fb79f99052ee07d00e1e999e27af6562aee6a2d57d381bf1e8ab8d5', 'public_key': '0xf6cd37284e1f2f488d303b7c7f291cf3321b18653f922fe84f1a0696d657f057', 'status': 'created'}


#import_wallet request

data[req] {'request_id': 'import_wallet', 'spider_id': 'xxxx', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun'}

#import_wallet response

import_wallet Resp {'address': '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6', 'balance': '9998.488', 'mnemonic': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'private_key': '0xcc52e76074649c744d4d4ff4bc38892788482a07fa45020d6388e212d068140993a40740fa38ab29093000efaa683a0ff477a3a43a6c5673b5ce480a1faf37da', 'public_key': '0x5c20e9ebb2263c82c2788f440490459ddb9bd0fa3f1e7e56452efaf691206370', 'status': 'imported'}


#pre_propose request
data[req] {'request_id': 'pre_propose', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'module_name': 'Balances', 'call_id': 'transfer', 'call_params': {'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 'value': 105}}

pre_propose Resp {'block_hash': '0x7efce0295cb0411580b0cac3133d94a6ba41ae2e56fb28f5a626052715ac9c18', 'call': "{'call_module': 'Balances', 'call_function': 'transfer', 'call_args': {'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 'value': 105000000000000}}", 'preimage_hash': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425', 'storageFee': 0.42}

#propose request
data[req] {'request_id': 'propose', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'preimage_hash': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425'}

#propose response
propose Resp {'PropIndex': 4, 'block_hash': '0xbfb7766ec80bfc61981dd594990f0171e2725e0bac2e7e92453a8e28a4327f10', 'launch_period': '5 minutes to be Launched', 'preimage_hash': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425'}

#second request
data[req] {'request_id': 'second', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'prop_index': 4}

#second response
second Resp {'block_hash': '0x0c943fe525dbfe24f63f03642a82a94cd0fc1bfd3218cec8038c7c5c28ee8dd2'}



data[req] {'request_id': 'get_ref', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'ref_index': 4}
RAW {
  "status": "Referendum not found"
}

DAO RAW RESPONSE {'status': 'Referendum not found'}
get_ref Resp {'status': 'Referendum not found'}



data[req] {'request_id': 'get_ref', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'ref_index': 4}
RAW {
  "status": "Referendum not found"
}

DAO RAW RESPONSE {'status': 'Referendum not found'}
get_ref Resp {'status': 'Referendum not found'}



data[req] {'request_id': 'get_ref', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'ref_index': 4}
RAW {
  "ayes": 0, 
  "end_block": 12000, 
  "nays": 0, 
  "proposal": "0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425", 
  "status": "Ongoing", 
  "total_votes": 0
}

DAO RAW RESPONSE {'ayes': 0, 'end_block': 12000, 'nays': 0, 'proposal': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425', 'status': 'Ongoing', 'total_votes': 0}
get_ref Resp {'ayes': 0, 'end_block': 12000, 'nays': 0, 'proposal': '0x79590dde16988b4c4f185198157deb6cc7e0deb0697aa1e42a95ff65e31fe425', 'status': 'Ongoing', 'total_votes': 0}



data[req] {'request_id': 'vote', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'ref_index': 4, 'vote': 'yes'}
RAW {
  "block_hash": "0xd2aeecd94ceb664f2b61da8fe1c79fe8d01fe03d333663119ea285b9715241ab", 
  "ref_index": 4, 
  "vote": "yes"
}

DAO RAW RESPONSE {'block_hash': '0xd2aeecd94ceb664f2b61da8fe1c79fe8d01fe03d333663119ea285b9715241ab', 'ref_index': 4, 'vote': 'yes'}
vote Resp {'block_hash': '0xd2aeecd94ceb664f2b61da8fe1c79fe8d01fe03d333663119ea285b9715241ab', 'ref_index': 4, 'vote': 'yes'}



data[req] {'request_id': 'get_props', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx'}
RAW {
  "current_proposals": 0
}

DAO RAW RESPONSE {'current_proposals': 0}
get_props Resp {'current_proposals': 0}



data[req] {'request_id': 'get_balance', 'phrase': 'sea enlist keen impulse fuel please parent cushion puppy repair leaf gun', 'spider_id': 'xxxx', 'address': '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6'}
RAW {
  "address": "5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6", 
  "balance": 9997999494026194
}

DAO RAW RESPONSE {'address': '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6', 'balance': 9997999494026194}
get_balance Resp {'address': '5E9W3GkF3BhjqVTadjCr87Urh6WkJKEdVSkg9qfLEjZdkCT6', 'balance': 9997999494026194}

"""