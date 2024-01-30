"""
Module for managing the execution environment on the local disk.

This module provides a class that handles the execution of code stored on the local
file system. It includes methods for uploading files to the execution environment,
running commands, and capturing the output.

Classes
-------
DiskExecutionEnv
    An execution environment that runs code on the local file system and captures
    the output of the execution.

Imports
-------
- subprocess: For running shell commands.
- time: For timing the execution of commands.
- Path: For handling file system paths.
- Optional, Tuple, Union: For type annotations.
- BaseExecutionEnv: For inheriting the base execution environment interface.
- FileStore: For managing file storage.
- FilesDict: For handling collections of files.
"""

import subprocess
import time

from pathlib import Path
from typing import Optional, Tuple, Union

from gpt_engineer.core.base_execution_env import BaseExecutionEnv
from gpt_engineer.core.default.file_store import FileStore
from gpt_engineer.core.files_dict import FilesDict


class DiskExecutionEnv(BaseExecutionEnv):
    """
    An execution environment that runs code on the local file system and captures
    the output of the execution.

    This class is responsible for executing code that is stored on disk. It ensures that
    the necessary entrypoint file exists and then runs the code using a subprocess. If the
    execution is interrupted by the user, it handles the interruption gracefully.

    Attributes
    ----------
    store : FileStore
        An instance of FileStore that manages the storage of files in the execution
        environment.

    Methods
    -------
    upload(files: FilesDict) -> "DiskExecutionEnv":
        Uploads a collection of files to the execution environment.

    download() -> FilesDict:
        Downloads all files from the execution environment as a FilesDict.

    popen(command: str) -> subprocess.Popen:
        Starts a subprocess with the given command and returns the Popen object.

    run(command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        Executes the given command in the execution environment and returns the
        standard output, standard error, and return code.
    """

    def __init__(self, path: Union[str, Path, None] = None):
        self.store = FileStore(path)

    def upload(self, files: FilesDict) -> "DiskExecutionEnv":
        self.store.upload(files)
        return self

    def download(self) -> FilesDict:
        return self.store.download()

    def popen(self, command: str) -> subprocess.Popen:
        p = subprocess.Popen(
            command,
            shell=True,
            cwd=self.store.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return p

    def run(self, command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        start = time.time()
        print("\n--- Start of run ---")
        # while running, also print the stdout and stderr
        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.store.working_dir,
            text=True,
            shell=True,
        )
        print("$", command)
        stdout_full, stderr_full = "", ""

        try:
            while p.poll() is None:
                assert p.stdout is not None
                assert p.stderr is not None
                stdout = p.stdout.readline()
                stderr = p.stderr.readline()
                if stdout:
                    print(stdout, end="")
                    stdout_full += stdout
                if stderr:
                    print(stderr, end="")
                    stderr_full += stderr
                if timeout and time.time() - start > timeout:
                    print("Timeout!")
                    p.kill()
                    raise TimeoutError()
        except KeyboardInterrupt:
            print()
            print("Stopping execution.")
            print("Execution stopped.")
            p.kill()
            print()
            print("--- Finished run ---\n")

        return stdout_full, stderr_full, p.returncode
