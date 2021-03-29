# SpiderDAO API

The API is used internally to handle communication between Router users and the Testnet, will be replaced by on the Router wallet, since now the router is low on storage space

- Flask-based API
- Runs on port :55551
- Receives DAO requests from external clients (Router clients)
- API design is defined inside the Python code `spiderdao_api.py`
- `cerberus` is used to validate API input schemas
- The current version of the API is intended for internal use only and subject to change 

## Run
    source ../spiderdao_env
    python3 spiderdao_api.py

API will start on http://127.0.0.1:55551