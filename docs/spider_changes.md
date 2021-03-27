## Summary of the changes in Polkadot codebase

- Cargo.toml

        path: polkadot/runtime/rococo
        desc: Modified to add democracy pallet and its deps to Rococo runtime build

- chain_spec.rs

        path: polkadot/node/service/src
        desc: Modified to add democracy pallet and its deps to the network storage and chainspec

- lib.rs

        path : polkadot/runtime/rococo/src
        desc : Modified to add democracy pallet and its deps to Rococo runtime source code,
        Contains chain constant (EnactmentPeriod, LaunchPeriod..etc), manual changes has //#S
