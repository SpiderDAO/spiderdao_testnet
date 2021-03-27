# SpiderDAO Discord Bot
A bot to test the Testnet functionalities outside of the Router

## Run
- Create a bot on Discord https://discordpy.readthedocs.io/en/latest/discord.html
- Set `BOT_TOKEN` and `pub_channel_id` in `spiderdao_env`

		source ../spiderdao_env
		python3 discord_bot.py

# Usage
	- Log into the discord bot server
	- Find [spidertest] Bot
	- "!" is the Bot command prefix

## Get available modules
	!helpall modules
Gets available modules to vote on

## Get single module help
	!helpmods [Module name]
	#Example
	!helpmods Balances

Shows available calls to vote for `Module name`
	
## Create a new wallet
	!wallet create

- Create a new wallet, returns generated seed phrase, address, public key and private key

## Import Exisiting wallet
	!wallet import `"SEED_PHRASE"` (Note the quotes) 
	
	#Example
	!wallet import "twelve words seed phrase generated previously by !wallet create"
	
	#Example
	!wallet import "throw leg electric envelope sea artist mountain globe cliff try umbrella picture"
 
- Imports existing wallet from seed phrase 

## Create a Proposal

	!propose [Module name] [function] [parameters]
	
	#Example
	!propose Balances transfer 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 46
	
	#Uses `transfer` function from `Balances` module to propose sending `46` (46 SPDR) to address `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY`

- Create a new proposal, returns the Preimage Hash, Proposal Index, Storage fee

## Second a Proposal
	!second [proposal_index]
	
	#Example (11 is the proposal index resulted from !propose command as mentioned above)
	!second 11 

- Second a Proposal by Proposal Index
	
### Once proposal Launched, a message will be sent to the public channel set in spiderdao_env notifying other users

- Notification message sample

		Referendum 11 Started from Proposal 11 by `user`
        To Vote call: !vote 11 [yes|no]

### Users can used the Referendum Index (11) to Vote and query Referendum status

## Vote
	!vote [Referendum_Index] [yes|no]
	
	#Example (yes Or no)
	!vote 11 yes

- Vote on a referendum
	
## Referendum Status

	!ref [Referendum_Index]
	#If no `Referendum_Index` passed, shows all Referendums

- Shows referendum state

## Show Balance

	!balance [address]

- Shows balance of `address`, if `address` is empty, shows current user's balance

## Show Proposals
	!proposals [proposal_index]
	#If no `proposal_index` passed, shows all proposals

- Shows proposals states