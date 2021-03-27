`Tested on Ubuntu 18.04 and 20.04`

## Setting SpiderDAO Env `spiderdao_env`

    #Passes the Node Websocket port to spiderdao.py [Mandatory]
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

    cd spiderdao_testnet
    #Set environment variables in `spiderdao_env`

    docker build -t spiderdaotestnet:latest .
    
    #Everything included in the container
    docker run -dit --env-file ./spiderdao_env -p 80:80 -p 443:443 -p 30333:30333 -p 9945:9945 -p 9933:9933 -p 55551:55551 -v nginxconf:/etc/nginx/ -v certs:/etc/ssl -v spiderdao_testnet:/home/spiderdao_testnet --name spiderdao_container spiderdaotestnet:latest /bin/bash
    
    #OR

    #Chain-only Run the chain only (Polkadot nodes and Rococo collator)
    docker run -dit --env-file ./spiderdao_env -p 9945:9945 --name spiderdao_container spiderdaotestnet:latest /bin/bash

    docker exec -it spiderdao_container /bin/bash -c "/home/spiderdao_testnet/spiderdao_testnet/spiderdao_testnet_start.sh"

## Docker image load from archive
If Docker image provided as an archived image

    docker load -i spiderdaotestnet_docker_image.tar.gz
    docker run -dit --env-file ./spiderdao_env -p 80:80 -p 443:443 -p 30333:30333 -p 9945:9945 -p 9933:9933 -p 55551:55551 -v nginxconf:/etc/nginx/ -v certs:/etc/ssl -v spiderdao_testnet:/home/spiderdao_testnet --name spiderdao_container spiderdaotestnet:latest /bin/bash
    docker exec -it spiderdao_container /bin/bash -c "/home/spiderdao_testnet/spiderdao_testnet/spiderdao_testnet_start.sh"

In the mapped volumes
* nginxconf:/etc/nginx/ : place your Hostname for the Node and API as described in below and in [nginx/README.md](nginx/README.md)
* certs:/etc/ssl: place your SSL certificates as described in below and in [nginx/README.md](nginx/README.md)

### For Chain-only run, SpiderDAO API and Discord bot can be started on the Host from the cloned directory as following:

Install Python dependencies

        pip3 install --no-deps -r requirements.txt

The API

        cd spiderdao_testnet
        source spiderdao_env
        cd api/
        python3 spiderdao_api.py #Starts on port 55551

The Discord Bot

        cd spiderdao_testnet
        source spiderdao_env
        cd discord_bot/
        python3 discord_bot.py

* Follow the guidelines in Readme files in each module's directory for correct usage 


# Manual Installation
## System dependencies

    apt update
    apt dist-upgrade
    apt install locales cmake bash-completion nano vim pkg-config sudo libssl-dev build-essential \
    clang libclang-dev curl apt-transport-https ca-certificates curl software-properties-common htop python3-pip cmake bmon \
    git libudev-dev libcurl4-openssl-dev ufw nginx wget psmisc

## Install Rust

    curl https://sh.rustup.rs -sSf | bash -s -- -y
    source $HOME/.cargo/env
    rustup install nightly-2020-10-01-x86_64-unknown-linux-gnu
    rustup target add wasm32-unknown-unknown --toolchain nightly-2020-10-01-x86_64-unknown-linux-gnu

## Clone SpiderDAO repo and Install Python dependencies
    git clone https://github.com/SpiderDAO/spiderdao_testnet
    cd spiderdao_testnet
    pip3 install --no-deps -r requirements.txt

## Clone and Build SpiderDAO's Polkadot fork
    #Back to parent directory
    cd ../

    #Forked Polkadot repo has changes described in spider_changes file
    git clone https://github.com/SpiderDAO/polkadot
    git fetch
    git checkout spiderdao-testnet

    #Build
    source $HOME/.cargo/env
    cargo build --release --features=real-overseer

## Clone and Build SpiderDAO's Cumulus fork
    #Back to parent directory
    cd ../

    git clone https://github.com/SpiderDAO/cumulus
    git fetch
    git checkout spiderdao-testnet

    #Build
    source $HOME/.cargo/env
    WASM_BUILD_TOOLCHAIN=nightly-2020-10-01 cargo +nightly-2020-10-01 build --release

Now SpiderDAO's Testnet dependencies are set and ready

    source spiderdao_env
## Run everything (Polkadot, Rococo-collators, Discord bot and SpiderDAO API)
    ./spiderdao_testnet_start.sh

## Runs Polkadot and Rococo-collators only
    cd scripts/
    ./spiderdao-local-parachain.sh

Find the Testnet on Polkadot Telemetry SpiderDAO_Testnet tab
The Testnet can be accessed from https://polkadot.js.org/apps/?rpc=ws://127.0.0.1:9945

## Run Discord Bot and API only (Depends on the chain being up)
    cd scripts/
    ./spiderdao_start.sh

## Nginx Setup
Nginx is used as a reverse proxy for the API and accessing the network from external locations (not required for local setups) 
In `nginx.conf`
- Replace {HOST_...} placeholders with your hostnames
- Create Nginx ssl certificates if needed and replace the paths [/path/to/ssl/] in Nginx.conf with your paths

### Notes

- Polkadot and Cumulus Forks achieve two purposes:
    - Version freeze for both repos to keep SpiderDAO related changes isolated and under control
    - Changes to Polkadot codebase, mainly adding support to Democracy pallet

