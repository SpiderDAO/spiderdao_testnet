killall polkadot
killall rococo-collator

cd polkadot
./target/release/polkadot purge-chain -y 

cd ../cumulus
./target/release/rococo-collator purge-chain -y

./qkill.sh discord_bot.py
./qkill.sh spiderdao_api.py