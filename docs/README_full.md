# SpiderDAO

![](https://i.imgur.com/zlw9lZ3.png)

# About
SpiderDAO’s initial project on the Polkadot Ecosystem will be SpiderVPN. This service will provide a decentralised router-based VPN service for its users by using a dual-governance model which brings together hardware and software tools with on-chain elements. SpiderDAO aims to build a new set of standards for Decentralised Autonomous Organisations to counteract the unfair distribution of voting power. Combining hardware safeguards and leveraging the Polkadot consensus mechanism, SpiderDAO establishes a whale-resistant mechanism whilst creating a highly scalable, interoperable and stable governance system.

## Overview
SpiderDAO Testnet is based on Cumulus Rococo Parachain setup, with modifications in Polkadot codebase like adding Democracy, Treasury, Bounties and other pallets, for the current version of the testnet we're focusing on Democracy pallet.

## Version `1.7`

## Main components:
[SpiderDAO Architecture](imgs/diagrams.md#spiderdao-architecture)

SpiderDAO Testnet based on Cumulus/Rococo Parachain with 2 collators and 2 full nodes, with Democracy pallet enabled, users can join the testnet by creating a wallet using the SpiderConnect Router Dashboard or using the Discord bot, The Router Dashboard is communicating with the testnet through SpiderDAO API, because currently the router hardware has limited storage. A full feature fledged wallet will be hosted on the SpiderConnect router new platforms in the future.

The main changes from the upstream Democracy pallet are the duration of Launch period, Enactment period, Voting period

* Launch period : 7 hours for internal testing | 7 days for testnet release
* Enactment period : 7 hours for internal testing | 7 days for testnet release
* Voting period : 4 hours for internal testing | 4 days for testnet release
* Constant deposit for all transaction set as 100 SPDR forced in the API
* Release values are set in the Docker image

## SpiderDAO Governance Flowchart
[SpiderDAO Flowchart](imgs/diagrams.md#dao-flowchart)

Detailed Installation Instructions in [INSTALL.md](INSTALL.md)

## Setting SpiderDAO Env `spiderdao_env`

    #Set the Node Websocket address and port to spiderdao.py [Mandatory]
    export NODE_URL=ws://127.0.0.1:9945

    #Discord Bot token
    export BOT_TOKEN=

    #Discord Public channel ID
    export pub_channel_id=

    #The chain modules which users are allowed to create proposals
    export BOT_MODULES=Balances,Council,Bounties,Treasury

    #Set sudo key, for sudo transactions
    export SUDO_KEY=

    #String message to be shown in Discord messages 
    export LAUNCH_PERIOD="Proposal Launching in 7 Days"

# Automatic/Ready Installation
## Docker setup
    git clone https://github.com/SpiderDAO/spiderdao_testnet

    #Set environment variables in `spiderdao_env`

    docker build -t spiderdaotestnet:latest .
    
    docker run -dit --env-file ./spiderdao_env -p 80:80 -p 443:443 -p 30333:30333 -p 9945:9945 -p 9933:9933 -p 55551:55551 -v nginxconf:/etc/nginx/ -v certs:/etc/ssl -v spiderdao_testnet:/home/spiderdao_testnet --name spiderdao_container spiderdaotestnet:latest /bin/bash
    #OR 
    docker run -dit --env-file ./spiderdao_env -p 9945:9945 --name spiderdao_container spiderdaotestnet:latest /bin/bash

    docker exec -it spiderdao_container /bin/bash -c "/home/spiderdao_testnet/spiderdao_testnet/spiderdao_testnet_start.sh"

# Note About Democracy Pallet
After careful consideration by the development team, we decided to go with using the runtime pallets route which suits our needs more than smart contracts, especially when we scale up. In addition, because of the availability of substrate runtime pallets, we can get flawless upgrades.

# Credits
## Special thanks goes to 
-  https://github.com/polkascan/ as we used both https://github.com/polkascan/py-scale-codec & https://github.com/polkascan/py-substrate-interface repos for our DAO framework development.
-  https://github.com/w3f for their help answering all our enquires.

# Licence
[APACHE 2.0](LICENSE)
