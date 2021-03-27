#!/bin/bash

cd ../../
cd polkadot

# Manual Edit _plain.json and build
#./target/release/polkadot build-spec --chain rococo-local --disable-default-bootnode > spiderdao-local-cfde-real-overseer_plain.json
#./target/release/polkadot build-spec --chain spiderdao-local-cfde-real-overseer_plain.json --disable-default-bootnode --raw > spiderdao-rococo-local-cfde-real-overseer.json
# Generate a raw chain spec for dist!
#./target/release/polkadot build-spec --chain rococo-local --disable-default-bootnode --raw > spiderdao-rococo-local-cfde-real-overseer.json

#Start validator nodes
# Alice
nohup ./target/release/polkadot --chain spiderdao-rococo-local-cfde-real-overseer.json --alice --ws-port 9945 --name SpiderTestNode --ws-external --rpc-cors all  --tmp --telemetry-url 'wss://telemetry.polkadot.io/submit/ 0' > alice_node.out &

sleep 3
# Bob
nohup ./target/release/polkadot --chain spiderdao-rococo-local-cfde-real-overseer.json --bob --tmp --port 30334 > bob_node.out &
sleep 3

##Start collator nodes and the parachain
cd ../cumulus
################### https://github.com/scs/integritee-parachain

# Export genesis state
# --parachain-id [8787] as an example that can be chosen freely. Make sure to everywhere use the same parachain id
./target/release/rococo-collator export-genesis-state --parachain-id 8787 > genesis-state

# Export genesis wasm
./target/release/rococo-collator export-genesis-wasm > genesis-wasm
sleep 1

# Collator1
nohup ./target/release/rococo-collator --collator --tmp --parachain-id 8787 --port 40335 --ws-port 9946 -- --execution wasm --chain ../polkadot/spiderdao-rococo-local-cfde-real-overseer.json --port 30335 --rpc-cors all  > collator1_node.out &
sleep 3
# Collator2
nohup ./target/release/rococo-collator --collator --tmp --parachain-id 8787 --port 40336 --ws-port 9947 -- --execution wasm --chain ../polkadot/spiderdao-rococo-local-cfde-real-overseer.json --port 30336 --rpc-cors all  > collator2_node.out &
sleep 3
# Parachain Full Node 1
nohup ./target/release/rococo-collator --tmp --parachain-id 8787 --port 40337 --ws-port 9948 -- --execution wasm --chain ../polkadot/spiderdao-rococo-local-cfde-real-overseer.json --port 30337 --wasm-execution=compiled  > parachain_full_node.out &
sleep 3

