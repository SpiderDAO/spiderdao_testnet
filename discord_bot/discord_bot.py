import discord
from discord.ext import commands
from substrateinterface import SubstrateInterface, Keypair
import asyncio
import os
import sys

sys.path.insert(0, '../src')
from spiderdao import *

botcalls = botcalls_mods

for bc in botcalls:
    botcalls[bc] = sorted(botcalls[bc])

botmods_list = sorted(botcalls.keys())

# GLOBALS
TOKEN = os.environ.get('BOT_TOKEN')
pub_channel_id = int(os.environ.get('pub_channel_id'))

#private key of sudo key, used to set testnet tokens for bot users
SUDO_KEY = os.environ.get('SUDO_KEY') 

launch_period = os.environ.get('LAUNCH_PERIOD')

bot_users = {}
bot = commands.Bot(command_prefix='!')

pub_channel = bot.get_channel(pub_channel_id)

async def cb_ch(event_index, lev, ebh):
    if event_index == "1e01": #'event_id': 'Tabled'
        print("CALLED send_referendum_started")
        await send_referendum_started(lev, ebh)
    
    if event_index == "1e04" or event_index == "1e05": #'event_id': 'Passed' or 'NotPassed'
        print("CALLED send_referendum_results")
        await send_referendum_results(lev, ebh)

    return

# Chain events listener

chain_evs = None
try:
    chain_evs = SpiderDaoChain(chain_events_cb=cb_ch)
except:
    print("Couldn't start SpiderDAOChain, check that the chain is running")
    sys.exit(0)

print("SpiderDAO BOT START")

democracy_commands = [
    "!helpall modules",
    "!helpmods [module name]", 
    "!wallet [create|import [seed phrase]]", 
    "!propose [module name] [module call] [call parameters]",
    "!second [proposal index]",
    "!vote [referendum index] [yes|no]", 
    "!balance [address]", 
    "!ref [referendum index]", 
    "!proposals [proposal index]",
    "!send [address] [value]"
]

@bot.event
async def on_command_error(ctx, error):
    
    rep_cmd_err = f"{str(error)}, Available Commands:\n"+" 👈\n".join(democracy_commands)
    print("BOT ERROR", str(error))
    await ctx.send(rep_cmd_err)
    return

@bot.command(name='hi', help='Shows bot commands')
async def bot_greet(ctx, *arg):
    print(*arg)
    await ctx.send("Available Commands:\n"+" 👈\n".join(democracy_commands))

@bot.command(name='wallet', help='Create or Import wallet')
async def bot_wallet(ctx, *arg):

    if str(ctx.channel.type) != "private":
        await ctx.send("Use !wallet commands in Private channel only")
        return

    async with ctx.typing():
        cmd = arg[0].strip()

        if cmd == "create":
            spdr = SpiderDaoInterface()
            n_keypair = spdr.create_wallet()

            #Set initial balance for Discord bot Testnet users
            current_balance = spdr.get_balance(n_keypair.ss58_address)
            if current_balance == 0 or current_balance is None:
                if not spdr.set_balance(n_keypair.ss58_address):
                    await ctx.send(f"{ctx.author}: Error Transferring initial balance")
                    return

            balance = spdr.get_balance(n_keypair.ss58_address)
            balance = str(round(float(balance / spdr.CHAIN_DEC), 4))

            wallet_info = f" \
            Seed phrase: `{n_keypair.mnemonic}`\n \
            Address: `{n_keypair.ss58_address}`\n \
            Public Key: `{n_keypair.public_key}`\n \
            Private key: `{n_keypair.private_key}`\n \
            Current Balance: `{balance}` SPDR`\n"
            bot_users[ctx.author] = {
                "keypair" : n_keypair
            }

            await ctx.send(f"Wallet Created:\n{wallet_info}")
        
        elif cmd == "import":
            print("AUTHOR", ctx.author)
            mnemonic = arg[1].strip()

            spdr = None
            try:
                spdr = SpiderDaoInterface(mnemonic=mnemonic)
            except:
                await ctx.send(f"Error Importing Wallet")
                return

            if spdr is None:
                await ctx.send(f"Error Importing Wallet")
                return

            n_keypair = spdr.keypair
            current_balance = 0
            try:
                current_balance = spdr.get_balance(n_keypair.ss58_address)
                if current_balance == 0 or current_balance is None:
                    if not spdr.set_balance(n_keypair.ss58_address):
                        await ctx.send(f"{ctx.author}: Error Transferring initial balance")
                        return
            except:
                await ctx.send(f"Wallet not found")
                return

            balance = spdr.get_balance(n_keypair.ss58_address)
            balance = str(round(float(balance / spdr.CHAIN_DEC), 4))

            wallet_info = f" \
            Seed phrase: `{n_keypair.mnemonic}`\n \
            Address: `{n_keypair.ss58_address}`\n \
            Public Key: `{n_keypair.public_key}`\n \
            Private key: `{n_keypair.private_key}`\n \
            Current Balance: `{balance}` SPDR`\n"
            bot_users[ctx.author] = {
                "keypair" : n_keypair
            }
            await ctx.send(f"Wallet Imported:\n{wallet_info}")
        else:
           await ctx.send(f"{cmd}: Wrong wallet command, usage !wallet create or !wallet import [seed_phrase]") 

    return

@bot.command(name='helpall', help='Bot Help')
async def bot_help(ctx, *arg):
    print(*arg)
    
    h_m = "modules"
    if "" == str(*arg).strip():
        h_m = "modules"
    else:
        h_m = arg[0].strip()

    if h_m == "modules":
        res = ""
        smo = botmods_list
        for s in smo:
            res = res + "🧩 " + s + "\n"
        res = str(res)
        res = res[:min(len(res), 300)]
        msg_rep = "Available Modules: " + str(len(botcalls.keys())) + " | 👉 !helpmods [Module name] for module calls" + "\n"+"\n"+res
        await ctx.send(msg_rep)
    if h_m == "calls":
        res = chn.get_modules_calls()
        res = str(res)
        res = res[:min(len(res), 100)]
        await ctx.send("Available Commands:\n"+"\n"+res)
    if h_m == "call":
        mod_id = arg[1]
        call_id = arg[2]
        res = chn.get_module_call(mod_id, call_id)
        res = str(res)
        res = res[:min(len(res), 100)]
        await ctx.send("Available Commands:\n"+res)
    
    return

@bot.command(name='helpmods', help='Modules usage')
async def bot_help(ctx, *arg):
    print(*arg)

    if len(arg) != 1:
        await ctx.send(f"!helpmods [module_name]")
        return

    h_m = arg[0].strip()
    if h_m not in botcalls:
        await ctx.send(f"{h_m} not found 🔧")
        return
    
    res = "\n".join(botcalls[h_m])
    res = res[:min(len(res), 1900)]
    msg_rep = f"Module `🧩{h_m}` Calls:\n\n"+res
    await ctx.send(msg_rep)

    return

@bot.command(name='send', help='Send balance to other SpiderDAO testnet users')
async def send_balance(ctx, *arg):
    
    if len(arg) != 2:
        await ctx.send(f"!send [address] [value], e.g !send 5CiPPseXPECbkjWCa6MnjNokrgYjMqmKndv2rSnekmSK2DjL 10")
        return

    spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"])
    address = str(arg[0])
    value = str(arg[1])

    balance = {}
    bot_msg = ""
    try:
        balance = spdr.send_balance(address, value)
    except Exception as e:
        print("Balance sending error", e)
        await ctx.send(f"!send [address] [value], e.g !send 5CiPPseXPECbkjWCa6MnjNokrgYjMqmKndv2rSnekmSK2DjL 10")
        return

    if "error" in balance:
        bot_msg = "Balance sending error: " + str(balance["error"])
        await ctx.send(bot_msg)
    else:
       bot_msg = "Balance Sent Successfully: " + str(balance["success"]) + " Block Hash: " + str(balance["block_hash"])
       await ctx.send(bot_msg)

    return


@bot.command(name='propose', help='Start a proposal')
async def bot_propose(ctx, *arg):
    # !propose [module] [call_id] [args]
    # !propose balance transfer [dest_user, value]
    if ctx.author not in bot_users:
        await ctx.send(f"{ctx.author}: No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"])

    proposal = {}
    preimage_hash = ""
    storageFee = ""

    async with ctx.typing():
        proposal = spdr.pre_propose(arg)
        if "error" in proposal:
            await ctx.send("1: propose: Something wrong happend!" + str(proposal))
            return

        preimage_hash = proposal["preimage_hash"]
        storageFee = str(proposal["storageFee"])
        bot_msg = f"Preimage Hash: `{preimage_hash}`, Proposal Storage Fee: `{storageFee}`"
        await ctx.send(bot_msg)

        await ctx.send(f"Confirm Submitting Proposal? (y/n)")
        msg = await bot.wait_for("message", check=lambda m:m.author == ctx.author and m.channel.id == ctx.channel.id)
        rep = str(msg.content).strip().lower()
        if rep not in ("y", "yes"):
            await ctx.send("🔴 Proposal Cancelled, Bye!")
            return
        else:
            await ctx.send("🟢 Submitting Proposal")

    async with ctx.typing():
        try:
            
            proposal = spdr.propose(proposal["preimage_hash"])
            ev = spdr.substrate.get_events(block_hash=proposal["block_hash"])

            block_hash = proposal["block_hash"]
            PropIndex = proposal["PropIndex"]
            launch_period = proposal["launch_period"]

            msg_rep = f"Proposal Submitted:\n \
            ✍️ Preimage Hash `{preimage_hash}` \n \
            🛡️ Block Hash `{block_hash}` \n \
            👉 Proposal Index: `{PropIndex}` \n \
            🕑 `{launch_period}` "

            #Proposals off-chain storage
            #spdr.db_set_user(PropIndex, str(ctx.author)) 

            print(f"{ctx.author}: MSG REP PROP", msg_rep)
            await ctx.send(msg_rep)
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            await ctx.send("2: propose: Something wrong happend!" + str(proposal))
    
    return


@bot.command(name='second', help='Second a proposal')
async def bot_second(ctx, *arg):

    if ctx.author not in bot_users:
        await ctx.send("No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    async with ctx.typing():
        try:
            prop_index = str(arg[0]) ##RECHECK
            spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"])

            if not proposals_db.exists(prop_index):
                await ctx.send(f"Wrong proposal")
                return

            proposal = spdr.second(prop_index)
            if "error" in proposal:
                await ctx.send("second: error!" + str(proposal["error"]))
                return

            await ctx.send(f"✅ You `Seconded` Proposal `{prop_index}`")

        except Exception as e:
            print(f"{ctx.author}: Error", str(e))
            await ctx.send("Something wrong happend!, `!second`")
    return

@bot.command(name='vote', help='Vote on a Referendum')
async def bot_vote(ctx, *arg):

    if ctx.author not in bot_users:
        await ctx.send("No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    ref_index = -1
    vote = ""

    try:
        ref_index = int(arg[0])
        vote = arg[1]
    except:
        await ctx.send(f"Wrong Input: !vote ref_index [yes|no], i.e !vote 1 yes")
        return

    async with ctx.typing():
        spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"])
        vote = spdr.vote(ref_index, vote)
        if "error" in vote:
            await ctx.send("vote error! " + vote["error"])
            return
        
        res_vote = ""
        if vote["vote"].lower() == "yes":
            res_vote = "✅ " + vote["vote"].capitalize()
        else:
            res_vote = "❌ " + vote["vote"].capitalize()

        bot_msg = f"You Voted `{res_vote}` on Referendum `{ref_index}`"
        await ctx.send(bot_msg)
    return

@bot.command(name='balance', help='Get balance of current user address or any other chain address')
async def bot_getbalance(ctx, *arg):

    if ctx.author not in bot_users:
        await ctx.send("No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    addr = ""
    if len(arg) == 1:
        addr = arg[0]
    else:
        addr =  bot_users[ctx.author]["keypair"].ss58_address

    async with ctx.typing():
        spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"]) #RECHECK
        balance = spdr.get_balance(addr)
        if balance is None:
            await ctx.send("balance: Something wrong happend!")
            return

        balance = str(round(float(balance / spdr.CHAIN_DEC), 4))

        msg_rep = f"💰 Balance `{balance}` SPDR"
        print(f"{ctx.author} {msg_rep}")
        await ctx.send(msg_rep)

@bot.command(name='ref', help='Get Referendum info `!ref [ref_index]`')
async def bot_getrefinfo(ctx, *arg):

    if ctx.author not in bot_users:
        await ctx.send("No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    _all = True
    ref_idx = ""
    ref_msg = "Referendum Not Found"

    if len(arg) == 1:
        _all = False
        ref_idx = str(arg[0])

    spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"]) #RECHECK

    print(f"{ctx.author}: REFINFO", ref_idx, _all)

    ret_ref_list = []
    async with ctx.typing():
        if _all:
            ref_list = spdr.get_all_refs()
            if len(ref_list) == 0:
                await ctx.send(ref_msg)
                return

            for r in ref_list:
                ret_ref_list.append(r["ref_msg"])

            ref_msg = "\n\n".join(ret_ref_list)
        else:
            ref_msg = spdr.get_ref_status(ref_idx)
            if ref_msg is None:
                ref_msg = f"🎗 Referendum `{ref_idx}` is Not Found"
            else:
                ref_msg = ref_msg["ref_msg"]

    print("REFMSG", ref_msg)
    await ctx.send(ref_msg)

@bot.command(name='proposals', help='Get Proposals')
async def bot_getprops(ctx, *arg):

    if ctx.author not in bot_users:
        await ctx.send("No Wallet found, Create/Import Wallet `!wallet create|import`")
        return

    props_msg = "Proposal Not Found"
    async with ctx.typing():
        _all = True
        prop_idx = ""
        

        if len(arg) == 1:
            _all = False
            prop_idx = str(arg[0])

        spdr = SpiderDaoInterface(keypair=bot_users[ctx.author]["keypair"])

        print(f"{ctx.author}: PROPINFO", prop_idx, _all)

        prop = None
        ret_prop_list = []
        if _all:
            props_list = spdr.get_all_proposals()
            if len(props_list) == 0:
                await ctx.send(props_msg)
                return

            for p in props_list:
                ret_prop_list.append(p["prop_msg"])

            props_msg = "\n\n".join(ret_prop_list)
        else:
            props_msg = spdr.get_proposal(prop_idx)
            if props_msg is not None:
                props_msg = props_msg["prop_msg"]
        
    print("Sending prop_msg", ctx.author, props_msg)
    await ctx.send(props_msg)

def parse_refstarted(ledx):

    ref_dic = {}
    for e in ledx:
        if e.event_index == "1e01": #Tabled
            for ep in list(e.params):
                if ep["type"] == "PropIndex":
                    ref_dic["PropIndex"] = str(ep["value"])

                if ep["type"] == "Vec<AccountId>":
                    ref_dic["pub_key"] = str(ep["value"][0])

        if e.event_index == "1e03": #Started
            for ep in list(e.params):
                if ep["type"] == "ReferendumIndex":
                    ref_dic["ReferendumIndex"] = str(ep["value"])

                if ep["type"] == "VoteThreshold":
                    ref_dic["VoteThreshold"] = str(ep["value"])

    ref_dic["username"] = None
    for u in bot_users:
        if bot_users[u]["keypair"].public_key == ref_dic["pub_key"]:
            ref_dic["username"] = bot_users[u]["keypair"].ss58_address

    if ref_dic["username"] is None:
        ref_dic["username"] = Keypair(public_key=str(ref_dic["pub_key"]), ss58_format=42).ss58_address

    return ref_dic

dup_ref_started = []
loop = asyncio.get_event_loop() #recheck
async def send_referendum_started(ledx, ebh):

    global dup_ref_started
    
    dex = parse_refstarted(ledx)
    pub_channel = bot.get_channel(pub_channel_id)
    ReferendumIndex = str(dex["ReferendumIndex"])
    PropIndex = dex["PropIndex"]
    username = dex["username"]
    msg_rep = f"Referendum `{ReferendumIndex}` Started from Proposal `{PropIndex}` by `{str(username)}` \n \
        To Vote call: !vote `{ReferendumIndex}` [yes|no]"

    if ReferendumIndex in dup_ref_started:
        print("send_referendum_started DUPLICATE", msg_rep)
        if len(dup_ref_started) > 5: 
            dup_ref_started = []
        return

    dup_ref_started.append(ReferendumIndex) #Event is sent two times for some reason, this removes duplicate event

    print("*** send_referendum_started MSG_REP", msg_rep)
    loop.create_task(pub_channel.send(msg_rep))
    print("REF DEX", dex)
    return

def parse_refresult(ledx):

    ref_dic = {}
    for e in ledx:
        if e.event_index == "1e04": #Tabled
            for ep in list(e.params):
                if ep["type"] == "ReferendumIndex":
                    ref_dic["ReferendumIndex"] = str(ep["value"])
                    ref_dic["result"] = "Approved"

        if e.event_index == "1e05": #Started
            for ep in list(e.params):
                if ep["type"] == "ReferendumIndex":
                    ref_dic["ReferendumIndex"] = str(ep["value"])
                    ref_dic["result"] = "Not Approved"

    return ref_dic

dup_ref_results = []
async def send_referendum_results(ledx, ebh):

    global dup_ref_results

    dex = parse_refresult(ledx)
    pub_channel = bot.get_channel(pub_channel_id)
    ReferendumIndex = str(dex["ReferendumIndex"])
    result = dex["result"]
    msg_rep = f"Referendum `{ReferendumIndex}` Result `{result}`"

    if ReferendumIndex in dup_ref_results:
        print("send_referendum_results DUPLICATE", msg_rep)
        if len(dup_ref_results) > 5:
            dup_ref_results = []
        return

    dup_ref_results.append(ReferendumIndex) #Event is sent two times for some reason, this removes duplicate event

    loop.create_task(pub_channel.send(msg_rep))

    return

bot.run(TOKEN)
