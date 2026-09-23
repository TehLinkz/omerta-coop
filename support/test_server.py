import asyncio
from pathlib import Path
import struct
import tempfile
import unittest

from server import Server
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

    async def client(self, profile, name=b'Player', token=TOKEN):
        reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
        c = Client(reader, writer)
        self.clients.append(c)
        result = await c.call('rpcCoopHello', token, profile, name, 3)
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
