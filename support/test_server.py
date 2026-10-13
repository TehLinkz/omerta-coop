import asyncio
from pathlib import Path
import struct
import tempfile
import unittest

from server import Server, MISSIONS, BASE_MISSIONS
from wire import decode, encode, rpc_packet, unpack_rpc

TOKEN = 'test-token-only-not-for-deployment-123'


class Client:
    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer
        self.events = []
        self.seq = 0

    async def receive(self):
        size = struct.unpack('>I', await self.reader.readexactly(4))[0]
        return unpack_rpc(await self.reader.readexactly(size))

    async def event(self, expected):
        for i, (name, args) in enumerate(self.events):
            if name == expected:
                self.events.pop(i)
                return args
        while True:
            name, args = await asyncio.wait_for(self.receive(), 2)
            if name == expected:
                return args
            self.events.append((name, args))

    async def send(self, name, *args):
        self.writer.write(rpc_packet(name, *args))
        await self.writer.drain()

    async def call(self, name, *args):
        self.seq += 1
        request = self.seq
        await self.send('rpcRfcRequest', request, name, *args)
        while True:
            method, result = await asyncio.wait_for(self.receive(), 2)
            if method == 'rpcRfcResult' and result[0] == request:
                return result[1:]
            self.events.append((method, result))


class WireTests(unittest.TestCase):
    def test_binary_and_nil_arguments_survive(self):
        body = rpc_packet('rpcEvent', b'\x00\xffpayload', None, -123, {2: False})[4:]
        self.assertEqual(unpack_rpc(body), ('rpcEvent', [b'\x00\xffpayload', None, -123, {2: False}]))

    def test_malformed_values_rejected(self):
        for body in (b's\xff\xff\xff\xff', b'n\x00\x00\x00\x01x', b'x', encode({1:b'a'}) + b'x'):
            with self.assertRaises(ValueError):
                decode(body)


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.instance = Server(TOKEN, self.temp.name)
        self.listener = await asyncio.start_server(self.instance.accept, '127.0.0.1', 0)
        self.port = self.listener.sockets[0].getsockname()[1]
        self.clients = []

    async def client(self, profile, name=b'Player', token=TOKEN, missions=None, features=None):
        reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
        c = Client(reader, writer)
        self.clients.append(c)
        args = [] if missions is None else [{m:True for m in missions}]
        if features is not None:
            args = [{m:True for m in (missions if missions is not None else BASE_MISSIONS)}, features]
        result = await c.call('rpcCoopHello', token, profile, name, 3, 2, *args)
        return c, result

    async def asyncTearDown(self):
        for c in self.clients:
            c.writer.close()
            await c.writer.wait_closed()
        self.listener.close()
        await self.listener.wait_closed()
        await asyncio.sleep(0.05)
        self.temp.cleanup()

    async def test_rejects_wrong_token_and_duplicate_identity(self):
        c, result = await self.client('profile-0001', token='wrong')
        self.assertEqual(result, [b'failed'])
        c, result = await self.client('profile-0001')
        self.assertEqual(result[0], False)
        c, result = await self.client('profile-0001')
        self.assertEqual(result, [b'full'])

    async def ping_pair(self, legacy=False):
        c1, _ = await self.client('ping-player-1', features={b'map_ping_v1':True})
        c2, _ = await self.client('ping-player-2', features=None if legacy else {b'map_ping_v1':True})
        await c1.call('rpcStartMatch', b'Coop_BankHeist', True)
        await c2.call('rpcStartMatch', b'Coop_BankHeist', True)
        game = (await c1.event('rpcChallengeAccepted'))[0]
        await c2.event('rpcChallengeAccepted')
        await c1.call('rpcJoinGame', 'Gangs', game)
        await c2.call('rpcJoinGame', 'Gangs', game)
        return c1, c2, game

    async def test_map_ping_reaches_both_players_and_not_game_events(self):
        c1,c2,game = await self.ping_pair()
        self.assertEqual(await c1.call('rpcCoopMapPing',game,12345,67890,0),[False])
        expected = [game,1,12345,67890,0]
        self.assertEqual(await c1.event('rpcCoopMapPing'),expected)
        self.assertEqual(await c2.event('rpcCoopMapPing'),expected)
        self.assertEqual(await c2.call('rpcCoopMapPing',game,200,300,-5),[False])
        self.assertEqual((await c1.event('rpcCoopMapPing'))[1],2)
        self.assertFalse(any(e[0]=='rpcEvent' for e in c1.events+c2.events))

    async def test_map_ping_validates_match_coordinates_and_cooldown(self):
        c1,c2,game = await self.ping_pair()
        for coords in [(True,2,3),(-1,2,3),(10000001,2,3),(1,2,1000001),(b'x',2,3)]:
            self.assertEqual(await c1.call('rpcCoopMapPing',game,*coords),[b'param'])
        self.assertEqual(await c1.call('rpcCoopMapPing',game+1,1,2,3),[b'failed'])
        self.assertEqual(await c1.call('rpcCoopMapPing',game,1,2,3),[False])
        self.assertEqual(await c1.call('rpcCoopMapPing',game,1,2,3),[b'rate limited'])
        await c1.call('rpcLeaveGame')
        self.assertEqual(await c1.call('rpcCoopMapPing',game,1,2,3),[b'failed'])

    async def test_map_ping_never_sends_unknown_rpc_to_legacy_client(self):
        c1,c2,game = await self.ping_pair(legacy=True)
        self.assertEqual(await c1.call('rpcCoopMapPing',game,10,20,30),[False])
        await c2.call('rpcPing')
        self.assertFalse(any(e[0]=='rpcCoopMapPing' for e in c2.events))
        self.assertEqual(await c2.call('rpcCoopMapPing',game,10,20,30),[b'failed'])

    async def test_map_ping_not_queued_for_loading_partner(self):
        c1,c2,game = await self.ping_pair()
        peer2 = list(self.instance.peers.values())[1]
        peer2.match.joined.remove(peer2)
        self.assertEqual(await c1.call('rpcCoopMapPing',game,10,20,30),[False])
        self.assertEqual(peer2.match.pending[peer2],[])
        await c2.call('rpcJoinGame','Gangs',game)
        await c2.call('rpcPing')
        self.assertFalse(any(e[0]=='rpcCoopMapPing' for e in c2.events))

    async def test_no_token_host_accepts_new_and_legacy_clients(self):
        self.instance.token = b''
        c1, r1 = await self.client('profile-0001', token='')
        c2, r2 = await self.client('profile-0002', token=TOKEN)
        self.assertEqual(r1[0], False)
        self.assertEqual(r2[0], False)
        status = await c1.call('rpcCoopUpdate', {}, {})
        self.assertEqual(status[1][b'friends'][r2[1]], b'Player')

    async def test_pair_join_relay_complete_and_persist(self):
        c1, r1 = await self.client('profile-0001', b'Host')
        c2, r2 = await self.client('profile-0002', b'Friend')
        status = await c1.call('rpcCoopUpdate', {}, {})
        self.assertEqual(status[1][b'friends'], {r2[1]: b'Friend'})
        self.assertEqual(status[1][b'status'][r2[1]], b'O')
        payload = b'\x00\xffsaved-gang'
        self.assertEqual(await c1.call('rpcSaveStorage', payload), [False])
        self.assertEqual(await c1.call('rpcLoadStorage', False), [False, payload])
        self.assertEqual(await c2.call('rpcLoadStorage', False), [False, False])
        mission = b'Coop_BankHeist'
        await c1.call('rpcStartMatch', mission, True)
        await c2.call('rpcStartMatch', mission, True)
        e1, e2 = await c1.event('rpcChallengeAccepted'), await c2.event('rpcChallengeAccepted')
        self.assertEqual(e1[:3], e2[:3])
        game = e1[0]
        self.assertEqual(await c1.call('rpcJoinGame', 'Gangs', game), [False, 1])
        await c1.send('rpcSyncPlayersData', b'gang1', b'Host', 120000, game)
        self.assertEqual(await c2.call('rpcJoinGame', 'Gangs', game), [False, 2])
        self.assertEqual(await c2.event('rpcSyncPlayersData'), [b'gang1', b'Host', 120000, game])
        await c2.send('rpcStartGame', 12345)
        self.assertEqual(await c1.event('rpcStartGame'), [12345])
        await c1.send('rpcSyncEvent', b'TestAction', b'\xff\x00native-payload', True)
        self.assertEqual(await c1.event('rpcEvent'), [b'TestAction', b'\xff\x00native-payload', True])
        self.assertEqual(await c2.event('rpcEvent'), [b'TestAction', b'\xff\x00native-payload', True])
        gains = {1: {b'money': 500}, 2: {b'money': 250}}
        await c1.call('rpcCoopVictory', True, True, gains)
        await c2.call('rpcCoopVictory', True, True, gains)
        self.assertEqual(await c1.event('rpcCoopVictoryConfirmed'), [True, {b'money': 500}])
        self.assertEqual(await c2.event('rpcCoopVictoryConfirmed'), [True, {b'money': 250}])
        self.assertEqual(await c1.call('rpcLeaveGame'), [False])
        self.assertEqual(await c2.event('rpcDropped'), [1, True])

    async def test_host_difficulty_is_snapshotted_for_both_players(self):
        import json
        settings = Path(self.temp.name) / 'settings.json'
        settings.write_text(json.dumps({'difficulty':'insane'}))
        self.instance.settings_path = settings
        c1, r1 = await self.client('profile-0001')
        c2, r2 = await self.client('profile-0002')
        await c1.call('rpcStartMatch', b'Coop_BankHeist', True)
        await c2.call('rpcStartMatch', b'Coop_BankHeist', True)
        self.assertEqual(await c1.event('rpcCoopRules'), [2,b'insane'])
        self.assertEqual(await c2.event('rpcCoopRules'), [2,b'insane'])
        self.assertEqual(self.instance.peers[r1[1]].match.difficulty,'insane')
        settings.write_text(json.dumps({'difficulty':'easy'}))
        self.assertEqual(self.instance.peers[r1[1]].match.difficulty,'insane')
        self.assertEqual(await c2.call('rpcCoopRules',2,'easy'),[b'unsupported'])
        self.assertEqual(self.instance.peers[r1[1]].match.difficulty,'insane')

    async def test_older_patch_is_rejected_before_login(self):
        reader,writer=await asyncio.open_connection('127.0.0.1',self.port)
        c=Client(reader,writer);self.clients.append(c)
        result=await c.call('rpcCoopHello',TOKEN,'profile-0001','Old client',3)
        self.assertIn(b'Update both PCs',result[0])
        self.assertEqual(len(self.instance.peers),0)

    async def test_expansion_quickmatch_join_and_relay(self):
        c1,r1=await self.client('profile-0001',missions=MISSIONS)
        c2,r2=await self.client('profile-0002',missions=MISSIONS)
        self.assertIn(b'Coop_Fire',(await c1.call('rpcCountMatch'))[1])
        self.assertEqual(await c1.call('rpcStartMatch',b'Coop_Fire',True),[False])
        self.assertEqual(await c2.call('rpcStartMatch',b'Coop_Fire',True),[False])
        a=await c1.event('rpcChallengeAccepted');b=await c2.event('rpcChallengeAccepted')
        self.assertEqual(a[1],b'Coop_Fire');self.assertEqual(a[:3],b[:3])
        self.assertEqual(await c1.call('rpcJoinGame','Gangs',a[0]),[False,1])
        self.assertEqual(await c2.call('rpcJoinGame','Gangs',a[0]),[False,2])
        await c1.send('rpcSyncEvent',b'FireAction',b'opaque-native-payload')
        self.assertEqual(await c2.event('rpcEvent'),[b'FireAction',b'opaque-native-payload'])

    async def test_expansion_requires_both_clients_and_legacy_is_base_only(self):
        c1,r1=await self.client('profile-0001',missions=MISSIONS)
        c2,r2=await self.client('profile-0002')
        self.assertEqual(await c2.call('rpcStartMatch',b'Coop_Fire',True),[b'map missing'])
        self.assertEqual(await c1.call('rpcCoopUpdate',{r2[1]:b'Coop_Fire'},{}),[b'map missing'])
        self.assertIsNone(self.instance.peers[r1[1]].match)
        self.assertNotIn(b'Coop_Fire',(await c2.call('rpcCountMatch'))[1])

    async def test_random_matches_selected_expansion_when_both_have_it(self):
        c1,r1=await self.client('profile-0001',missions=MISSIONS)
        c2,r2=await self.client('profile-0002',missions=MISSIONS)
        await c1.call('rpcStartMatch',b'coop_random',True)
        await c2.call('rpcStartMatch',b'Coop_Fire',True)
        self.assertEqual((await c1.event('rpcChallengeAccepted'))[1],b'Coop_Fire')

    async def test_random_uses_only_common_missions(self):
        c1,r1=await self.client('profile-0001',missions=MISSIONS)
        c2,r2=await self.client('profile-0002',missions=BASE_MISSIONS)
        await c1.call('rpcStartMatch',b'coop_random',True)
        await c2.call('rpcStartMatch',b'coop_random',True)
        self.assertIn((await c1.event('rpcChallengeAccepted'))[1],BASE_MISSIONS)

    async def test_expansion_invitation_requires_acceptance(self):
        c1,r1=await self.client('profile-0001',missions=MISSIONS)
        c2,r2=await self.client('profile-0002',missions=MISSIONS)
        await c1.call('rpcCoopUpdate',{r2[1]:b'Coop_Fire'},{})
        self.assertIsNone(self.instance.peers[r1[1]].match)
        await c2.call('rpcCoopUpdate',{r1[1]:b'Coop_Fire'},{})
        self.assertEqual((await c1.event('rpcChallengeAccepted'))[1],b'Coop_Fire')

    async def test_challenge_requires_acceptance(self):
        c1, r1 = await self.client('profile-0001')
        c2, r2 = await self.client('profile-0002')
        mission = b'Coop_Prisonbreak'
        await c1.call('rpcCoopUpdate', {r2[1]: mission}, {})
        result = await c2.call('rpcCoopUpdate', {}, {})
        self.assertEqual(result[1][b'challengers'], {r1[1]: mission})
        self.assertIsNone(self.instance.peers[r1[1]].match)
        await c2.call('rpcCoopUpdate', {r1[1]: mission}, {})
        self.assertEqual((await c1.event('rpcChallengeAccepted'))[1], mission)


if __name__ == '__main__':
    unittest.main(verbosity=2)
