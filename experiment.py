import base64
import json
import os.path
import shutil
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from sys import argv
from time import sleep
from typing import Tuple, Optional

from deluge.config import Config
from deluge_client.client import DelugeRPCClient
from torrentool.api import Torrent


@dataclass(frozen=True)
class ExperimentConfig:
    tracker_url: str
    root_path: Path


class AuthFile:
    def __init__(self, path: Path):
        auth = {}
        with path.open('r', encoding='utf-8') as infile:
            for line in infile:
                username, password, _ = line.split(':')
                auth[username] = password

        self.passwords = auth


class TorrentClient:
    def __init__(self, root: Path):
        self.root = root
        self.downloads = root / 'downloads'
        self.state = root / 'state'
        self.config = Config(filename=os.path.abspath(root / 'core.conf'))
        self.auth = AuthFile(root / 'auth')

        self._rpc: Optional[DelugeRPCClient] = None

    def create_dataset(
            self,
            announce_url: str,
            name: str,
            size_bytes: int
    ) -> Tuple[Path, bytes]:
        data_root = self.downloads / name
        data_root.mkdir(parents=True, exist_ok=False)
        data_file = data_root / 'datafile.bin'

        random_bytes = os.urandom(size_bytes)
        with data_file.open('wb') as outfile:
            outfile.write(random_bytes)

        torrent_file = self.downloads / f'{name}.torrent'
        torrent_meta = Torrent.create_from(data_root)
        torrent_meta.announce_urls = announce_url
        torrent_meta.name = name
        torrent_meta.to_file(os.path.abspath(torrent_file))

        buffer = BytesIO()
        buffer.write(torrent_meta.to_string())

        return torrent_file, base64.b64encode(buffer.getvalue())

    def clear(self):
        shutil.rmtree(self.downloads)
        shutil.rmtree(self.state)

    def connect(self) -> 'TorrentClient':
        client = DelugeRPCClient(
            host=self.config['listen_interface'],
            port=self.config['daemon_port'],
            username='localclient',
            password=self.auth.passwords['localclient'],
        )
        client.connect()
        self._rpc = client
        return self

    @property
    def rpc(self) -> DelugeRPCClient:
        if self._rpc is None:
            self.connect()
        return self._rpc

    def wait_for_completion(self, torrent_name: str):
        while True:
            response = self.rpc.core.get_torrents_status({'name': torrent_name}, [])
            assert len(response) == 1
            status = list(response.values())[0]
            if status[b'is_finished']:
                return
            sleep(0.5)


def main(config: ExperimentConfig):
    root_path = Path(config.root_path)

    client1 = TorrentClient(root_path / 'client1')
    client2 = TorrentClient(root_path / 'client2')

    print("1 - Create dataset.")
    torrent_file, b64dump = client1.create_dataset(
        announce_url=config.tracker_url,
        name='dataset1',
        size_bytes=1024 * 1024 * 50
    )

    print("2 - Publish to seeder.")
    # Creates seeder.
    client1.rpc.core.add_torrent_file(
        filename='dataset1.torrent',
        filedump=b64dump,
        options=dict()
    )

    print("3 - Publish to leecher.")
    # Creates leecher.
    client2.rpc.core.add_torrent_file(
        filename='dataset1.torrent',
        filedump=b64dump,
        options=dict()
    )

    print("4 - Wait for completion.")
    client2.wait_for_completion('dataset1')

    print("5 - Clear.")


def parse_args() -> ExperimentConfig:
    if len(argv) != 2:
        print("Experiment configuration missing.")
        sys.exit(-1)

    return ExperimentConfig(
        **json.loads(Path(argv[1]).read_text()),
    )


if __name__ == '__main__':
    main(parse_args())
