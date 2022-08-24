"""
Azure Blob storage

More file operation examples:
https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/storage/azure-storage-blob/samples/blob_samples_directory_interface.py
"""

import logging
import re
from pathlib import Path
from typing import *

from azure.storage.blob import (BlobClient, BlobServiceClient,  # noqa
                                ContainerClient)

from jgutils import fileops as fl
from jgutils import functions as f
from jgutils.logger import get_log
from jgutils.secrets import SecretsManager

log = get_log(__name__)

# azure blob logs every http request by default
logging.getLogger('azure.core.pipeline.policies').setLevel(logging.WARNING)


class BlobStorage():
    def __init__(self, container: Union[str, Path]) -> None:
        """

        Parameters
        ----------
        container : str, optional
            container to use by default, by default 'jambot-app'
        """
        creds = SecretsManager('azure_blob.yaml').load
        self.client = BlobServiceClient.from_connection_string(
            creds['connection_string'])

        # pass in full dir, but only use name
        _p_local = None
        if isinstance(container, Path):
            _p_local = container
            fl.check_path(_p_local)
            container = container.name

        self._p_local = _p_local
        self.container = container

    @property
    def p_local(self) -> Path:
        """Local directory to upload/download to/from"""
        if self._p_local is None:
            raise RuntimeError('self.p_local not set!')

        return self._p_local

    def get_container(self, container: Union[str, ContainerClient] = None) -> ContainerClient:
        """Get container object

        Parameters
        ----------
        container : Union[str, ContainerClient]
            container/container name

        Returns
        -------
        ContainerClient
        """

        # container already init
        if isinstance(container, ContainerClient):
            return container

        container = container or self.container
        return self.client.get_container_client(container)

    def clear_container(
            self,
            container: Union[str, ContainerClient] = None,
            match: str = '.') -> None:
        """Delete all files in container

        Parameters
        ----------
        container : Union[str, ContainerClient]
            container name
        match : str, optional
            only delete if filename matches pattern
        """
        container = self.get_container(container)
        blob_list = [b.name for b in container.list_blobs()
                     if re.search(match, b.name, flags=re.IGNORECASE)]

        # Delete blobs
        container.delete_blobs(*blob_list)

    def upload_dir(
            self,
            p: Path = None,
            container: Union[str, ContainerClient] = None,
            mirror: bool = True,
            match: str = '.') -> None:
        """Upload entire dir files to container

        Parameters
        ----------
        p : Path
            dir to upload, default self.p_local
        container : Union[str, ContainerClient], optional
        mirror : bool, optional
            if true, delete all contents from container first
        match : str, optional
            only upload if filename matches pattern
        """
        if p is None:
            p = self.p_local

        self._validate_dir(p)
        container = self.get_container(container)

        if mirror:
            self.clear_container(container, match=match)

        i = 0
        for _p in p.iterdir():
            if not _p.is_dir():
                if re.search(match, _p.name, flags=re.IGNORECASE):
                    self.upload_file(p=_p, container=container, _log=False)
                    i += 1

        log.info(
            f'Uploaded [{i}] file(s) to container "{container.container_name}"')

    def download_dir(
            self,
            p: Path = None,
            container: Union[str, ContainerClient] = None,
            mirror: bool = True,
            match: str = '.') -> None:
        """Download entire container to local dir

        Parameters
        ----------
        p : Path
            dir to download to
        container : Union[str, ContainerClient], optional
        mirror : bool, optional
            if true, clear local dir first, by default True
        match : str, optional
            only download if filename matches pattern
        """
        if p is None:
            p = self.p_local

        self._validate_dir(p)
        container = self.get_container(container)

        if mirror:
            for _p in p.iterdir():
                if re.search(match, _p.name, flags=re.IGNORECASE):
                    _p.unlink()

        # blob here is BlobProperties
        i = 0
        try:
            for blob in container.list_blobs():

                # limit files to download w re search
                if re.search(match, blob.name, flags=re.IGNORECASE):
                    self.download_file(
                        p=p / blob.name, container=container, _log=False)

                    i += 1
        except Exception as e:
            msg = f'Failed to download files from container "{container.container_name}"'
            # cm.discord(msg, channel='err', log=log.warning)
            raise e

        log.info(
            f'Downloaded [{i}] file(s) from container "{container.container_name}"')

    def download_file(
            self,
            p: Union[Path, str],
            container: Union[str, ContainerClient] = None,
            _log: bool = True) -> Path:
        """Download file from container and save to local file

        Parameters
        ----------
        p : Union[Path, str]
            path to save to, p.name will be used to find file in blob
            - if str, must have p_local set
        container : str, optional
        """
        if isinstance(p, str):
            p = self.p_local / p

        container = self.get_container(container)
        blob = container.get_blob_client(p.name)

        fl.check_path(p)

        with open(p, 'wb') as file:
            file.write(blob.download_blob().readall())

        if _log:
            log.info(
                f'Downloaded "{blob.blob_name}" from container "{container.container_name}"')

        return p

    def upload_file(
            self,
            p: Path,
            container: Union[str, ContainerClient] = None,
            _log: bool = True) -> None:
        """Save local file to container

        Parameters
        ----------
        p : Path
            Path obj to upload to blob storage
        container : str, optional
            container name, by default self.container
        """
        container = self.get_container(container)

        if not p.exists():
            raise FileNotFoundError(f'Data file: "{p.name}" does not exist.')

        with open(p, 'rb') as file:
            blob = container.upload_blob(
                name=p.name, data=file, overwrite=True)

        if _log:
            log.info(
                f'Uploaded "{blob.blob_name}" to container "{container.container_name}"')

    def show_containers(self) -> None:
        """Show list of container names"""
        names = [c.name for c in self.client.list_containers()]
        f.pretty_dict(names)

    def list_files(self, container: str = None, match: str = '.') -> List[str]:
        """Get list of files in container

        Parameters
        ----------
        container : str, optional
            container to show files in, default self.container
        match : str, optional
            list if filename matches pattern

        Returns
        -------
        List[str]
            list of files in container
        """
        _container = self.get_container(container)
        return sorted([b.name for b in _container.list_blobs()
                       if re.search(match, b.name, flags=re.IGNORECASE)])

    def show_files(self, container: str = None, **kw) -> None:
        """Print list of files in container

        Parameters
        ----------
        container : str, optional
            container to show files in, default self.container
        """
        f.pretty_dict(self.list_files(container, **kw))

    def create_container(self, name: str) -> None:
        """Wrapper to create container in storage account

        Parameters
        ----------
        name : str
            name of container
        """
        self.client.create_container(name)

    def _validate_dir(self, p: Path) -> None:
        """Check if path is valid directory

        Parameters
        ----------
        p : Path
            path to check
        """
        if not p.is_dir():
            raise ValueError(f'p is not a directory: "{p}"')
