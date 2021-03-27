# build SpiderDAO Testnet
FROM ubuntu:focal as builder

LABEL maintainer="SpiderDAO"
ARG RUST_VERSION="nightly-2020-10-01-x86_64-unknown-linux-gnu"
ARG spiderdao_dir="spiderdao_testnet"
ARG polkadot_dir="polkadot"
ARG cumulus_dir="cumulus"
ARG SPIDERDAO_GIT_REPO="https://github.com/SpiderDAO/spiderdao_testnet.git"
ARG POLKADOT_GIT_REPO="https://github.com/SpiderDAO/polkadot"
ARG CUMULUS_GIT_REPO="https://github.com/SpiderDAO/cumulus"
ARG SPIDERDAO_GIT_BRANCH="main"
ARG POLKADOT_GIT_BRANCH="spiderdao-testnet"
ARG CUMULUS_GIT_BRANCH="spiderdao-democracy-mods"
ARG DEBIAN_FRONTEND=noninteractive
#ARG CACHEBUST=1 

WORKDIR /home/spiderdao_testnet
#DEPS
RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install -y locales cmake bash-completion nano vim pkg-config sudo libssl-dev build-essential \
clang libclang-dev curl apt-transport-https ca-certificates curl software-properties-common htop python3-pip cmake bmon \
apache2 git libudev-dev libcurl4-openssl-dev ufw nginx wget psmisc

#Fix locale
RUN rm -rf /var/lib/apt/lists/*
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
###############

#Clone SpiderDAO, Polkadot and Cumulus
RUN git clone ${SPIDERDAO_GIT_REPO} && cd ${spiderdao_dir} && git fetch &&  git checkout ${SPIDERDAO_GIT_BRANCH}
RUN git clone ${POLKADOT_GIT_REPO} && cd ${polkadot_dir} && git fetch &&  git checkout ${POLKADOT_GIT_BRANCH}
RUN git clone ${CUMULUS_GIT_REPO} && cd ${cumulus_dir} && git fetch && git checkout ${CUMULUS_GIT_BRANCH}

#Install Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

RUN . $HOME/.cargo/env; rustup install ${RUST_VERSION}
RUN . $HOME/.cargo/env; rustup target add wasm32-unknown-unknown --toolchain ${RUST_VERSION}

#Python Deps
COPY requirements.txt /home
WORKDIR /home
RUN pip3 install -U pip pip-upgrader
RUN pip3 install --no-deps -r requirements.txt; exit 0

#Build Polkadot and Cumulus/Rococo
WORKDIR /home/spiderdao_testnet/${polkadot_dir}
RUN . $HOME/.cargo/env; cargo build --release --features=real-overseer

WORKDIR /home/spiderdao_testnet/${cumulus_dir}
RUN . $HOME/.cargo/env;WASM_BUILD_TOOLCHAIN=nightly-2020-10-01 cargo +nightly-2020-10-01 build --release

#Configure Nginx
COPY nginx/nginx.conf /etc/nginx/

WORKDIR /home/spiderdao_testnet

COPY spiderdao_env .
COPY spiderdao_testnet_start.sh .

COPY chainspec/spiderdao-local-cfde-real-overseer_plain.json polkadot/
COPY chainspec/spiderdao-rococo-local-cfde-real-overseer.json polkadot/

EXPOSE 80 443 30333 9945 9933 55551

WORKDIR /home/spiderdao_testnet/spiderdao_testnet


CMD ["/home/spiderdao_testnet/spiderdao_testnet/spiderdao_testnet_start.sh"]


# docker build -t spiderdaotestnet:latest .
# docker run -dit --env-file ./spiderdao_env -p 80:80 -p 443:443 -p 30333:30333 -p 9945:9945 -p 9933:9933 -p 55551:55551 -v nginxconf:/etc/nginx/ -v certs:/etc/ssl -v spiderdao_testnet:/home/spiderdao_testnet --name spiderdao_container spiderdaotestnet:latest /bin/bash
# ##OR 
# docker run -dit --env-file ./spiderdao_env -p 9945:9945 --name spiderdao_container spiderdaotestnet:latest /bin/bash
# docker exec -it spiderdao_container /bin/bash -c "/home/spiderdao_testnet/spiderdao/spiderdao_testnet_start.sh"