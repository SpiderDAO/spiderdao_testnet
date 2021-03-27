import pytest
import sys

sys.path.insert(0, '../src')
from spiderdao import *

def test_parse_dict_args():

    spdr = SpiderDaoInterface()
    dict_args = {
    'module_name': 'Balances', 
    'call_id': 'transfer', 
    'call_params': {
        'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY',
        'value': 103
        }
    }

    result_args = {
        'module_name': 'Balances', 
        'call_id': 'transfer', 
        'params': {
            'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 
            'value': 103000000000000
            }
    }

    assert spdr.parse_dict_args(dict_args) == result_args


def test_parse_args():

    spdr = SpiderDaoInterface()

    #prop = "Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 103"
    prop = ("Balances", "transfer", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", "103")
    result_args = {
        'module_name': 'Balances', 
        'call_id': 'transfer', 
        'params': {
            'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 
            'value': 103000000000000
            }
    }

    assert spdr.parse_args(prop) == result_args

#Chain has to be running for this test to pass
def test_create_substrate_call():

    spdr = SpiderDaoInterface()

    call_params = {
        'module_name': 'Balances', 
        'call_id': 'transfer', 
        'params': {
            'dest': '5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY', 
            'value': 103000000000000
            }
    }

    encoded_proposal = "0x040000d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d0b0070698ead5d"

    _, _, result_encoded_proposal = spdr.create_substrate_call(call_params)
    assert result_encoded_proposal == encoded_proposal



