#!/bin/bash

#should sync repos


cp Cargo.toml ../polkadot/runtime/rococo
cp lib.rs ../polkadot/runtime/rococo/src
cp chain_spec.rs ../polkadot/node/service/src

#rococo-local-cfde-real-overseer.json