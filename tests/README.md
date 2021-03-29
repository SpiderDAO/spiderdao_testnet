# Testing guide

The code py-substrate-interface (which is properly unittested) to communicate and parse chain data

### Unit Test
    pytest test_spiderdao.py

### API Test
    # Run the API
    api/python3 spiderdao_api.py

    python3 test_spiderdao_api.py

API test consists of subsequent calls to the running API `../api/spiderdao_api.py` with a sample proposal