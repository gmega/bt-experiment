import base64
import os.path
from io import BytesIO
from pathlib import Path
from typing import Tuple

from deluge.config import Config
from torrentool.api import Torrent
from deluge_client.client import DelugeRPCClient

TRACKER_URL = 'http://localhost:6969/announce'


class Auth:
    def __init__(self, path: Path):
        auth = {}
        with path.open('r', encoding='utf-8') as infile:
            for line in infile:
                username, password, _ = line.split(':')
                auth[username] = password

        self.passwords = auth


def rpc_client(config_path: Path) -> DelugeRPCClient:
    config = Config(filename=os.path.abspath(config_path / 'core.conf'))
    auth = Auth(config_path / 'auth')
    return DelugeRPCClient(
        host='127.0.0.1',
        port=config['daemon_port'],
        username='localclient',
        password=auth.passwords['localclient'],
    )


def make_dataset(parent: Path, size_bytes: int, name: str, announce_url: str) -> Tuple[Path, Path, bytes]:
    if not parent.is_dir():
        raise Exception()

    data_root = parent / name
    data_root.mkdir(parents=True, exist_ok=False)
    data_file = data_root / 'datafile.bin'

    random_bytes = os.urandom(size_bytes)
    with data_file.open('wb') as outfile:
        outfile.write(random_bytes)

    torrent_file = parent / f'{name}.torrent'
    torrent_meta = Torrent.create_from(data_root)
    torrent_meta.announce_urls = announce_url
    torrent_meta.name = name
    torrent_meta.to_file(os.path.abspath(torrent_file))

    buffer = BytesIO()
    buffer.write(torrent_meta.to_string())

    return torrent_file, data_root, base64.b64encode(buffer.getvalue())


def main():
    root_path = Path('/home/giuliano/Work/Status/bittorrent-baseline/experiment-1/')

    client1 = rpc_client(root_path / 'client1')
    client2 = rpc_client(root_path / 'client2')

    torrent_file, _, b64dump = make_dataset(
        parent=root_path / 'client1' / 'downloads',
        size_bytes=1024 * 1024 * 50,
        name='dataset1',
        announce_url=TRACKER_URL,
    )

    client1.connect()
    client2.connect()

    client1.core.add_torrent_file(filename='dataset1.torrent', filedump=b64dump, options=dict())
    client1.core.add_torrent_file(filename='dataset1.torrent', filedump=b64dump, options=dict())


if __name__ == '__main__':
    main()
