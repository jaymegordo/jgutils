"""Simple file encryption management to avoid storing plaintext passwords"""
import json
import os
import re
from functools import cached_property
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from ruamel.yaml import YAML

from jgutils.helpers.enums import StrEnum


class CryptMethod(StrEnum):
    """Enum for encryption methods"""
    ENCRYPT = 'encrypt'
    DECRYPT = 'decrypt'


class SecretsManager():
    """Context manager to handle loading encrypted files from secrets folder

    Encrypts files with two structures:
    1. full - encrypt full file (read from /unencrypted, write to /encrypted)
    2. partial - encrypt defined keys in yaml file, read/write in-place in /mixed

    Parameters
    ----------
    load_filename : str
        Init with filename to load, call with .load property

    Examples
    --------
    >>> from jgutils.secrets import SecretsManager

    - load yaml dict automatically
    >>> m = SecretsManager().load('config.yaml')

    - re encrypt all files in /unencrypted after pws change
    >>> SecretsManager().encrypt_all_secrets()
    """
    ENV_KEY = 'JG_SECRET_KEY'

    # need to set path to secrets dir, could be different if frozen app
    _p_sec = os.getenv('P_SECRET', None)

    if _p_sec is None:
        raise RuntimeError(
            f'p_secret not set! p_secret: {_p_sec}')

    p_secret = Path(_p_sec)
    p_partial = p_secret / 'partial'
    p_full = p_secret / 'full'
    p_encrypted = p_full / 'encrypted'
    p_unencrypt = p_full / 'unencrypted'

    p_key = p_secret / 'jg.key'

    # prefixes for encrypting/decrypting partial yaml keys
    prefix_to_encrypt = '_'
    prefix_encrypted = 'e_'

    def _load_key(self) -> str:
        """Load key from secrets file, or from env variable"""

        if self.ENV_KEY in os.environ:
            # for remove services the key can be set as an env variable
            return os.environ[self.ENV_KEY]
        elif self.p_key.exists():
            # for local dev the key can be stored in a file
            return self.p_key.open('r').read()
        else:
            raise RuntimeError(
                f'Could not find key in env variable or file: {self.p_key}')

    @cached_property
    def key(self) -> str:
        """Load key from secrets dir"""
        return self._load_key()

    @cached_property
    def fernet(self) -> Fernet:
        """Create fernet object"""
        return Fernet(self.key)

    def _is_in_path(self, p_parent: Path, p: Path) -> bool:
        """Check if path is in parent path

        Parameters
        ----------
        p_parent : Path
            Parent path
        p : Path
            Path to check

        Returns
        -------
        bool
            True if p is in p_parent
        """

        # iterate through parent paths and check if equal to self.p_full
        return any(parent == p_parent for parent in p.parents)

    def _is_full(self, p: Path) -> bool:
        """Check if file is in self.p_full"""
        return self._is_in_path(self.p_full, p)

    def _is_partial(self, p: Path) -> bool:
        """Check if file is in self.p_partial"""
        return self._is_in_path(self.p_partial, p)

    @cached_property
    def yaml_obj(self) -> YAML:
        """Create ruamel yaml object with custom settings"""
        yaml_obj = YAML()
        yaml_obj.preserve_quotes = True
        yaml_obj.indent(mapping=2, sequence=4, offset=2)

        return yaml_obj

    def load_yaml(self, p: Path) -> dict:
        """Load yaml file with ruamel preserving anchors etc"""
        with p.open('r') as file:
            return self.yaml_obj.load(file)

    def write_yaml(self, p: Path, data: dict) -> None:
        """Write yaml file with ruamel"""
        with p.open('w') as file:
            self.yaml_obj.dump(data, file)

    def _new_key(self, method: CryptMethod, key: str) -> str:
        """Get replacement dict key for encrypt/decrypt

        eg:
            - '_password' -> 'e_password'
            - 'e_password' -> 'password'

        Parameters
        ----------
        method : CryptMethod
            Encrypt or decrypt
        key : str
            Key to create new key for

        Returns
        -------
        str
            New key
        """

        if method == CryptMethod.ENCRYPT:
            return re.sub(f'^{self.prefix_to_encrypt}', self.prefix_encrypted, key)

        elif method == CryptMethod.DECRYPT:
            return re.sub(f'^{self.prefix_encrypted}', '', key)

    def _encrypt_decrypt(self, method: CryptMethod, data: str) -> str:
        """Encrypt/decrypt string

        Parameters
        ----------
        method : CryptMethod
            Encrypt or decrypt
        data : str
            String to encrypt/decrypt

        Returns
        -------
        str
            Encrypted/decrypted string
        """
        funcs = {
            CryptMethod.ENCRYPT: self.fernet.encrypt,
            CryptMethod.DECRYPT: self.fernet.decrypt}

        return funcs[method](data.encode()).decode()

    def encrypt(self, data: str) -> str:
        """Convencience method to encrypt string

        Parameters
        ----------
        data : str
            String to encrypt

        Returns
        -------
        str

        """
        return self._encrypt_decrypt(CryptMethod.ENCRYPT, data)

    def decrypt(self, data: str) -> str:
        """Convencience method to decrypt string

        Parameters
        ----------
        data : str
            String to decrypt

        Returns
        -------
        str

        """
        return self._encrypt_decrypt(CryptMethod.DECRYPT, data)

    def is_encrypted(self, data: str) -> bool:
        """Check if string is encrypted"""
        try:
            self.decrypt(data)
        except InvalidToken:
            return False

        return True

    def _encrypt_decrypt_dict(self, method: CryptMethod, data: dict) -> None:
        """Encrypt/decrypt dictionary recursively
        - NOTE need to mutate in-place, otherwise loses yaml anchor/aliases

        Parameters
        ----------
        data : dict
            Dictionary to encrypt/decrypt
        method : CryptMethod
            Encrypt or decrypt
        """
        prefixes = {
            CryptMethod.DECRYPT: self.prefix_encrypted,
            CryptMethod.ENCRYPT: self.prefix_to_encrypt}

        for k, v in list(data.items()):
            if isinstance(v, dict):
                # call recursively
                self._encrypt_decrypt_dict(method, v)

            elif k.startswith(prefixes[method]):
                # create new key with 'e_' prefix and encrypt, or remove prefix and decrypt
                new_key = self._new_key(method, k)

                # Prevent overwriting existing unencrypted keys of same name
                if not new_key in data.keys():
                    data[new_key] = self._encrypt_decrypt(method, v)

                # can't delete old key when decrypting, linked by yaml anchor
                if method == CryptMethod.ENCRYPT:
                    # delete old key
                    del data[k]

    def _remove_encrypted_keys(self, data: dict) -> None:
        """Recursively remove keys that start with 'e_'

        Parameters
        ----------
        data : dict
            Dictionary to remove keys from
        """
        for k, v in list(data.items()):
            if isinstance(v, dict):
                # call recursively
                self._remove_encrypted_keys(v)

            elif k.startswith(self.prefix_encrypted):
                # delete key
                del data[k]

    def encrypt_yaml(self, data: dict) -> None:
        """Encrypt yaml data and return a new dictionary

        Parameters
        ----------
        data : dict
            Dictionary to encrypt
        """
        self._encrypt_decrypt_dict(CryptMethod.ENCRYPT, data)

    def decrypt_yaml(self, data: dict) -> None:
        """Decrypt yaml data and return a new dictionary

        Parameters
        ----------
        data : dict
            Dictionary to decrypt
        """
        self._encrypt_decrypt_dict(CryptMethod.DECRYPT, data)
        self._remove_encrypted_keys(data)

    def _get_path(self, name: str) -> Path:
        """Get unique path for filename in full/partial folder
        - NOTE names must be unique across both folders
        """
        paths = (self.p_partial, self.p_encrypted)

        # create dict of name: path
        data = {}

        for p_root in paths:
            for p in p_root.glob('*'):
                if p.is_file():
                    data[p.name] = p

        if not name in data.keys():
            raise FileNotFoundError(f'Couldn\'t find file: {name}')

        return data[name]

    def load(self, name: str) -> Any:  # noqa: ANN401
        """Get file from secrets folder by name and decrypt

        Parameters
        ----------
        name : str
            Name of file in secrets folder

        Returns
        -------
        Any
            Decrypted file
        """
        p = self._get_path(name)
        ext = p.suffix

        if self._is_full(p):
            data = self.decrypt_full_file(p=p)

            # convert to correct type if known extension
            if ext in ('.yaml', '.yml'):
                return yaml.load(data, Loader=yaml.Loader)
            elif ext == '.csv':
                return pd.read_csv(self.from_bytes(data))
            elif ext == '.json':
                return json.loads(data)

        elif self._is_partial(p):
            data = self.load_yaml(p=p)
            self.decrypt_yaml(data)
            return data

        else:
            raise RuntimeError(f'Unknown file: {p}')

    def encrypt_all_secrets(self):
        """
        Encrypt all files in /partial and /full/encrypted folders
        """
        i = 0

        # encrypt full files
        for p in self.p_unencrypt.glob('*'):
            self.encrypt_full_file(p)
            i += 1

        # encrypt partial files
        for p in self.p_partial.glob('*'):
            data = self.load_yaml(p)
            self.encrypt_yaml(data)
            self.write_yaml(p, data)
            i += 1

        print(f'Successfully encrypted [{i}] file(s).')  # noqa: T201

    def encrypt_full_file(self, p: Path, **kw) -> None:
        """Encrypt full file from /full/unencrypted folder

        Parameters
        ----------
        p : Path
            Path to file to encrypt
        """
        if not p.exists():
            raise FileNotFoundError(f'Couldn\'t find secret file: {p}')

        with p.open('rb') as file:
            file_data = file.read()

        self.write(file_data, name=p.name, **kw)

    def decrypt_full_file(self, p: Path) -> Any:  # noqa: ANN401
        """Decrypt file and return, DO NOT save back to disk"""
        with p.open('rb') as file:
            encrypted_data = file.read()

        return self.fernet.decrypt(encrypted_data)

    def write(self, file_data: bytes, name: str, p_save: Path | None = None, **kw):
        """Write unencrypted file back as encrypted

        Parameters
        ----------
        file_data : bytes
            File to encrypt and write back to secrets folder
        name : str
            filename including extension, eg credentials.yaml
        p_save : Path
            optional path to save encrypted file
        - NOTE only handles writing yaml files so far, need to add csv, txt ect
        """
        if p_save is None:
            p_save = self.p_encrypted

        p_save = p_save / name
        ext = name.split('.')[-1]

        # non-bytes dict passed back, encode as bytes here
        if ext in ('yaml', 'yml') and isinstance(file_data, dict):
            file_data = yaml.dump(file_data).encode()  # encode str as bytes

        encrypted_data = self.fernet.encrypt(file_data)

        with p_save.open('wb') as file:
            file.write(encrypted_data)

    @classmethod
    def write_key(cls) -> None:
        """Generates a key and save it into a file

        - NOTE should only need to run this once
        """

        # don't overwrite existing key
        if cls.p_key.exists():
            raise FileExistsError(f'Key file already exists: {cls.p_key}')

        key = Fernet.generate_key()

        with cls.p_key.open('wb') as file:
            file.write(key)

    def from_bytes(self, bytes: bytes) -> str:
        """Return string from bytes object
        - Useful for reading csv/excel data from bytes so far
        """
        result = str(bytes, 'UTF-8')
        return StringIO(result)
