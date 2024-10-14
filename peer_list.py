import json
import struct
from pathlib import Path
from typing import List, Tuple, cast

import requests
from torrentool.api import Torrent
from torrentool.bencode import Bencode
from hashlib import sha1
from socket import inet_ntoa

TRACKER_URL = 'http://127.0.0.1:6969/announce/'


def query_peers(path: Path):
    torrentfile = Torrent.from_file(path)

    response = requests.get(TRACKER_URL, params={'info_hash': info_hash(torrentfile)}).content
    status = Bencode.decode(response)
    peer_list = status['peers']
    status['peers'] = decode_compact_peers(peer_list.encode() if isinstance(peer_list, str) else peer_list)
    print(json.dumps(status, indent=2))


def decode_compact_peers(peers: bytes) -> List[Tuple[str, int]]:
    if len(peers) == 0:
        return []
    if len(peers) % 6 != 0:
        raise ValueError('Invalid compact peer list')

    encoded_records = [peers[(i * 6):(i + 1) * 6] for i in range(0, int(len(peers)/6))]
    return [
        (inet_ntoa(peer[:4]), cast(int, struct.unpack('>H', peer[4:])))
        for peer in encoded_records
    ]

def info_hash(torrentfile: Torrent) -> bytes:
    info = torrentfile._struct.get('info')
    return sha1(Bencode.encode(info)).digest()


query_peers(Path('/home/giuliano/Work/Status/bittorrent-baseline/experiment-1/client1/downloads/dataset1.torrent'))
