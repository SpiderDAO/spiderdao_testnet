# Example(s)

## propose_example.py

### Notes
- Integrates with SpiderDAO library and fully utilizes SpiderDAO's functionalities
- The proposals tested is a `Balances` `transfer` proposal
- The example uses the same proposal format as the discord e.g: `"Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 12"`
- Duplicate proposals aren't allowed, for testing you should at least change the value `12` in Balance Transfer proposals on every run

### Run
    source ../spiderdao_env
    python3 propose_example.py
