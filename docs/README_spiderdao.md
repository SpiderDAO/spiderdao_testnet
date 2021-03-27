## SpiderDAO.py 

SpiderDAO Interface, contains required function to created proposals on SpiderDAO Testnet

### Usage
	from spiderdao import *

	spdrdao = SpiderDaoInterface(node_url="ws://127.0.0.1:9945", chain_events_cb=chain_events_cb)

	spdrdao.create_wallet()
	spdrdao.get_balance("ADDRESS")


### Chain Events
A callback function can be set to `chain_events_cb`, to listen to any kind of chain events like a Referendum Started or Finished and many other events, a sample callback can be found in `propose_example.py`, the callback -if passed- will trigger the Chain events listener to start

	spdrdao = SpiderDaoInterface(node_url="ws://127.0.0.1:9945", chain_events_cb=chain_events_cb)

	async def chain_events_cb(event_index, lev, ebh):
		#print(lev)
		if event_index == "1e01": #'event_id': 'Tabled'
			print("CALLED send_referendum_started")
			msg_rep, ref_dic = await spdao.send_referendum_started(lev, ebh)
			print("ref_dic", msg_rep, ref_dic)
			spdao.vote(ref_dic["ReferendumIndex"], "yes")
		
		if event_index == "1e04" or event_index == "1e05": #'event_id': 'Passed' or 'NotPassed'
			print("CALLED show_referendum_result")
			await spdao.show_referendum_result(lev, ebh)
			
		return

