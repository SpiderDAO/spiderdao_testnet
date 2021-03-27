# Chain Specifications

Created as described here https://github.com/paritytech/cumulus/blob/master/README.md#launch-the-relay-chain

with few modifications:
* Generates Democracy pallet and its dependencies storage spec
* Set name and properties

        "name": "SpiderDAO_Testnet",
        ...
        "properties": {
        "ss58Format": 42,
        "tokenDecimals": 12,
        "tokenSymbol": "SPDR"
        },

* `spiderdao-rococo-local-cfde-real-overseer.json` is raw spec file, generated from `spiderdao-local-cfde-real-overseer_plain.json` as described in `scripts/spiderdao-local-parachain.sh` using the following commands

        ./target/release/polkadot build-spec --chain rococo-local --disable-default-bootnode > spiderdao-local-cfde-real-overseer_plain.json
        ./target/release/polkadot build-spec --chain spiderdao-local-cfde-real-overseer_plain.json --disable-default-bootnode --raw > spiderdao-rococo-local-cfde-real-overseer.json

* Then add mentioned modifications