"""Experimental two-player Omerta co-op lobby and ordered TCP relay."""
import argparse
import asyncio
import hashlib
import hmac
import json
import logging
from pathlib import Path
import secrets
import struct
import time

from wire import MAX_FRAME, rpc_packet, unpack_rpc

LOG = logging.getLogger('omerta')
RATING = {b'rating_coop': 120000, b'rating_pvsp': 120000}
BASE_MISSIONS = {b'Coop_BankHeist', b'Coop_Prisonbreak', b'Coop_LargeWarehouseFight'}
MISSIONS = BASE_MISSIONS | {b'Coop_Fire'}


class Peer:
    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer
        self.id = None
        self.profile = None
        self.name = b''
        self.room = b'English'
        self.version = None
        self.match = None
        self.queue = None
        self.missions = set(BASE_MISSIONS)
        self.challenges = {}

    async def send(self, name, *args):
        self.writer.write(rpc_packet(name, *args))
        await asyncio.wait_for(self.writer.drain(), 10)


class Match:
    def __init__(self, id_, players, mission):
        self.id, self.players, self.mission = id_, players, mission
        self.seed = secrets.randbelow(0x3fffffff)
        self.joined = set()
        self.pending = {p: [] for p in players}
        self.votes = {}
        self.finished = False
        self.hashes = {}


class Server:
    def __init__(self, token, state_dir, settings_path=None):
        self.settings_path = Path(settings_path) if settings_path else None
        self.token = token.encode()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.peers = {}
        self.next_id = 1
        self.next_match = 1
        self.started = time.monotonic()

    def storage(self, peer):
        return self.state_dir / (peer.profile + '.bin')

    async def accept(self, reader, writer):
        peer = Peer(reader, writer)
        try:
            while True:
                header = await asyncio.wait_for(reader.readexactly(4), 120 if peer.id else 15)
                size = struct.unpack('>I', header)[0]
                if not 1 <= size <= MAX_FRAME:
                    raise ValueError('frame size')
                body = await asyncio.wait_for(reader.readexactly(size), 30)
                name, args = unpack_rpc(body)
                if name == 'rpcRfcRequest':
                    if len(args) < 2 or type(args[0]) is not int or not isinstance(args[1], bytes):
                        raise ValueError('request envelope')
                    request_id, method, *params = args
                    result = await self.call(peer, method.decode('ascii'), params)
                    await peer.send('rpcRfcResult', request_id, *result)
                else:
                    await self.call(peer, name, args)
        except (asyncio.IncompleteReadError, ConnectionError, asyncio.TimeoutError):
            pass
        except Exception as exc:
            LOG.warning('Client %s rejected: %s', peer.id, exc)
        finally:
            if peer.id:
                await self.leave(peer, False)
                self.peers.pop(peer.id, None)
                LOG.info('Player %s disconnected', peer.id)
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    async def relay(self, peer, name, args, include_self=False):
        match = peer.match
        if not match or peer not in match.joined:
            return
        for target in match.players:
            if target is peer and not include_self:
                continue
            if target not in match.joined:
                if len(match.pending[target]) >= 100:
                    raise ValueError('pre-join queue limit')
                match.pending[target].append((name, args))
            else:
                await target.send(name, *args)

    async def leave(self, peer, graceful=True):
        match, peer.match = peer.match, None
        peer.queue = None
        if match:
            for other in match.players:
                if other is peer:
                    continue
                other.match = None
                try:
                    await other.send('rpcDropped', match.players.index(peer) + 1, graceful)
                except (ConnectionError, asyncio.TimeoutError):
                    pass

    async def pair(self, p1, p2, mission):
        if p1 is p2 or p1.match or p2.match or p1.version != p2.version:
            return False
        if mission not in p1.missions or mission not in p2.missions:
            return False
        rules = json.loads(self.settings_path.read_text()) if self.settings_path else {}
        difficulty = rules.get('difficulty', 'normal')
        if difficulty not in ('easy','normal','hard','insane'): raise ValueError('Invalid host difficulty')
        match = Match(self.next_match, [p1, p2], mission)
        match.difficulty = difficulty
        self.next_match += 1
        for p in match.players:
            p.match, p.queue = match, None
            p.challenges.clear()
        for p in match.players:
            await p.send('rpcCoopRules', 2, match.difficulty)
            await p.send('rpcChallengeAccepted', match.id, mission, match.seed, RATING)
        LOG.info('Match %s paired: players %s/%s, mission %s', match.id, p1.id, p2.id, mission.decode())
        return True

    async def call(self, p, method, a):
        if method == 'rpcCoopHello':
            if p.id: return [b'param']
            if len(a) not in (5,6) or a[4] != 2:
                return [b'Update both PCs to the difficulty-enabled patch']
            token, profile, name, version, patch_version = a[:5]
            available = a[5] if len(a) == 6 else {m: True for m in BASE_MISSIONS}
            if not isinstance(available, dict) or len(available) > len(MISSIONS) or any(m not in MISSIONS or enabled is not True for m, enabled in available.items()):
                return [b'param']
            if not isinstance(token, bytes) or (self.token and not hmac.compare_digest(token, self.token)):
                return [b'failed']
            if not isinstance(profile, bytes) or not 8 <= len(profile) <= 128:
                return [b'param']
            profile_hash = hashlib.sha256(profile).hexdigest()
            if len(self.peers) >= 2 or any(q.profile == profile_hash for q in self.peers.values()):
                return [b'full']
            if not isinstance(name, bytes) or not 1 <= len(name) <= 40 or type(version) is not int:
                return [b'param']
            p.id, self.next_id = self.next_id, self.next_id + 1
            p.profile, p.name, p.version = profile_hash, name, version
            p.missions = set(available)
            self.peers[p.id] = p
            LOG.info('Player %s connected, game network version %s', p.id, version)
            return [False, p.id]
        if not p.id:
            raise ValueError('hello required')
        if method == 'rpcPing':
            return [False, int((time.monotonic() - self.started) * 1000) % 0x7fffffff]
        if method == 'rpcGetName':
            return [False, p.name]
        if method == 'rpcSetName':
            if not a or not isinstance(a[0], bytes) or not 1 <= len(a[0]) <= 40:
                return [b'param']
            p.name = a[0]
            return [False]
        if method == 'rpcGetRating':
            return [False, RATING]
        if method == 'rpcLoadStorage':
            path = self.storage(p)
            return [False, path.read_bytes() if path.exists() else False]
        if method == 'rpcSaveStorage':
            if not a or not isinstance(a[0], bytes) or len(a[0]) > 2 * 1024 * 1024:
                return [b'param']
            path = self.storage(p)
            temp = path.with_suffix('.tmp')
            temp.write_bytes(a[0])
            temp.replace(path)
            return [False]
        if method == 'rpcCoopUpdate':
            challenges = a[0] if a and isinstance(a[0], dict) else {}
            rejects = a[1] if len(a) > 1 and isinstance(a[1], dict) else {}
            for other_id in rejects:
                other = self.peers.get(other_id)
                if other:
                    other.challenges.pop(p.id, None)
                p.challenges.pop(other_id, None)
            for other_id, mission in challenges.items():
                if mission not in p.missions:
                    return [b'map missing']
                other = self.peers.get(other_id)
                if not other or other is p:
                    continue
                if mission not in other.missions:
                    return [b'map missing']
                p.challenges[other_id] = mission
                if other.challenges.get(p.id) == mission:
                    await self.pair(other, p, mission)
            others = [q for q in self.peers.values() if q is not p and q.version == p.version]
            return [False, {
                b'friends': {q.id: q.name for q in others},
                b'status': {q.id: b'P' if q.match else b'O' for q in others},
                b'challenged': p.challenges.copy(),
                b'challengers': {q.id: q.challenges[p.id] for q in others if p.id in q.challenges},
            }]
        if method == 'rpcJoinChatRoom':
            if len(a) > 1 and isinstance(a[1], bytes):
                p.room = a[1]
            return [False, p.room, b'Private co-op prototype', len(self.peers)]
        if method == 'rpcEnumChatRooms':
            return [False, {p.room: len(self.peers)}]
        if method == 'rpcEnumRoomGuests':
            return [False, [q.name for q in self.peers.values()], len(self.peers)]
        if method == 'rpcLeaveChatRoom':
            return [False]
        if method == 'rpcChatMsg':
            if not a or not isinstance(a[0], bytes) or len(a[0]) > 2000:
                return [b'param']
            # Chat stays within this explicitly selected private two-player service.
            for q in list(self.peers.values()):
                await q.send('rpcChatMsg', p.name, a[0], False)
            return [False]
        if method == 'rpcImportFriends':
            return [False, {}]
        if method == 'rpcGetIdOf':
            return [False, next((q.id for q in self.peers.values() if a and q.name == a[0]), False)]
        if method == 'rpcStartMatch':
            mission = a[0] if a else None
            if mission != b'coop_random' and mission not in MISSIONS:
                return [b'param']
            if mission != b'coop_random' and mission not in p.missions:
                return [b'map missing']
            if p.match:
                return [b'failed']
            p.queue = mission
            for other in list(self.peers.values()):
                if other is p or not other.queue or other.match:
                    continue
                choices = p.missions & other.missions
                if mission != b'coop_random': choices &= {mission}
                if other.queue != b'coop_random': choices &= {other.queue}
                if choices and await self.pair(other, p, secrets.choice(sorted(choices))):
                    break
            return [False]
        if method == 'rpcGetMatchMission':
            return [False, p.queue or False]
        if method == 'rpcCancelMatch':
            p.queue = None
            return [False]
        if method == 'rpcCountMatch':
            counts = {m: sum(q.queue == m for q in self.peers.values()) for m in p.missions}
            counts[b'coop_random'] = sum(q.queue == b'coop_random' for q in self.peers.values())
            return [False, counts]
        if method == 'rpcJoinGame':
            if not p.match or len(a) != 2 or a[0] != b'Gangs' or a[1] != p.match.id:
                return [b'failed']
            match = p.match
            match.joined.add(p)
            # Defer buffered peer messages until the RFC result establishes netInGame.
            async def flush():
                await asyncio.sleep(0.05)
                for name, args in match.pending[p]:
                    if p.match is match:
                        await p.send(name, *args)
                match.pending[p].clear()
            asyncio.create_task(flush())
            return [False, match.players.index(p) + 1]
        if method == 'rpcLeaveGame':
            await self.leave(p)
            return [False]
        if method in ('rpcSyncPlayersData', 'rpcStartGame', 'rpcChangeLoadingStatus', 'rpcMissingMission'):
            await self.relay(p, method, a)
            return [False]
        if method in ('rpcEvent', 'rpcSyncEvent'):
            await self.relay(p, 'rpcEvent', a, include_self=method == 'rpcSyncEvent')
            return [False]
        if method == 'rpcPlayerHash':
            if p.match and len(a) >= 2:
                key = a[0]
                values = p.match.hashes.setdefault(key, {})
                values[p.id] = a[1]
                if len(values) == 2:
                    if len(set(values.values())) != 1:
                        LOG.error('Match %s desync at hash sequence %s', p.match.id, key)
                        for other in p.match.players:
                            await other.send('rpcDesync', p.match.id)
                    p.match.hashes.pop(key, None)
                if len(p.match.hashes) > 2000:
                    raise ValueError('hash backlog limit')
            return [False]
        if method == 'rpcSetPause':
            await self.relay(p, 'rpcSetPause', a, include_self=True)
            return [False]
        if method == 'rpcCoopVictory':
            if not p.match or len(a) != 3 or not isinstance(a[0], bool) or a[1] is not True or not isinstance(a[2], dict):
                return [b'param']
            match = p.match
            if match.finished:
                return [False]
            match.votes[p.id] = a
            if len(match.votes) == 2:
                votes = list(match.votes.values())
                if votes[0] != votes[1]:
                    return [b'desync']
                match.finished = True
                for i, other in enumerate(match.players, 1):
                    gain = a[2].get(i, {}).get(b'money', 0)
                    if type(gain) is not int or not 0 <= gain <= 100000:
                        raise ValueError('invalid reward')
                    await other.send('rpcCoopVictoryConfirmed', a[0], {b'money': gain})
                LOG.info('Match %s completed', match.id)
            return [False]
        LOG.warning('Unhandled RPC: %s', method)
        return [b'unsupported']


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', action='append', help='Listen address; repeat for loopback plus a private VPN address')
    parser.add_argument('--port', type=int, default=50669)
    parser.add_argument('--settings', type=Path, default=Path(__file__).with_name('server-settings.json'))
    parser.add_argument('--state', type=Path, default=Path(__file__).with_name('state'))
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text())
    token = settings.get('token', '')
    if not isinstance(token, str) or (token and len(token) < 24):
        raise ValueError('Optional legacy token must be at least 24 characters')
    instance = Server(token, args.state, args.settings)
    addresses = args.bind or ['127.0.0.1']
    server = await asyncio.start_server(instance.accept, addresses, args.port, limit=MAX_FRAME + 4)
    LOG.info('EXPERIMENTAL relay listening on %s:%s; two-player validation required', ', '.join(addresses), args.port)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
