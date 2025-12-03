import asyncio
import json
import logging
import os
import platform
import re
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# pg0 configuration
BINARY_NAME = "pg0"
DEFAULT_PORT = 5555
DEFAULT_USERNAME = "hindsight"
DEFAULT_PASSWORD = "hindsight"
DEFAULT_DATABASE = "hindsight"


def get_platform_binary_name() -> str:
    """Get the appropriate binary name for the current platform.

    Supported platforms:
    - macOS ARM64 (darwin-aarch64)
    - Linux x86_64 (gnu)
    - Linux ARM64 (gnu)
    - Windows x86_64
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "aarch64"
    else:
        raise RuntimeError(
            f"Embedded PostgreSQL is not supported on architecture: {machine}. "
            f"Supported architectures: x86_64/amd64 (Linux, Windows), aarch64/arm64 (macOS, Linux)"
        )

    if system == "darwin" and arch == "aarch64":
        return "pg0-darwin-aarch64"
    elif system == "linux" and arch == "x86_64":
        return "pg0-linux-x86_64-gnu"
    elif system == "linux" and arch == "aarch64":
        return "pg0-linux-aarch64-gnu"
    elif system == "windows" and arch == "x86_64":
        return "pg0-windows-x86_64.exe"
    else:
        raise RuntimeError(
            f"Embedded PostgreSQL is not supported on {system}-{arch}. "
            f"Supported platforms: darwin-aarch64 (macOS ARM), linux-x86_64-gnu, linux-aarch64-gnu, windows-x86_64"
        )


def get_download_url(
    version: str = "latest",
    repo: str = "vectorize-io/pg0",
) -> str:
    """Get the download URL for pg0 binary."""
    binary_name = get_platform_binary_name()

    if version == "latest":
        return f"https://github.com/{repo}/releases/latest/download/{binary_name}"
    else:
        return f"https://github.com/{repo}/releases/download/{version}/{binary_name}"


def _find_pg0_binary() -> Optional[Path]:
    """Find pg0 binary in PATH or default install location."""
    # First check PATH
    pg0_in_path = shutil.which("pg0")
    if pg0_in_path:
        return Path(pg0_in_path)

    # Fall back to default install location
    default_path = Path.home() / ".hindsight" / "bin" / "pg0"
    if default_path.exists() and os.access(default_path, os.X_OK):
        return default_path

    return None


class EmbeddedPostgres:
    """
    Manages an embedded PostgreSQL server instance using pg0.

    This class handles:
    - Finding or downloading the pg0 CLI
    - Starting/stopping the PostgreSQL server
    - Getting the connection URI

    Example:
        pg = EmbeddedPostgres()
        await pg.ensure_installed()
        await pg.start()
        uri = await pg.get_uri()
        # ... use uri with asyncpg ...
        await pg.stop()
    """

    def __init__(
        self,
        version: str = "latest",
        port: int = DEFAULT_PORT,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
        database: str = DEFAULT_DATABASE,
        name: str = "hindsight",
    ):
        """
        Initialize the embedded PostgreSQL manager.

        Args:
            version: Version of pg0 to download if not found. Defaults to "latest"
            port: Port to listen on. Defaults to 5555
            username: Username for the database. Defaults to "hindsight"
            password: Password for the database. Defaults to "hindsight"
            database: Database name to create. Defaults to "hindsight"
            name: Instance name for pg0. Defaults to "hindsight"
        """
        self.version = version
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.name = name

        # Will be set when binary is found/installed
        self._binary_path: Optional[Path] = _find_pg0_binary()

    @property
    def binary_path(self) -> Path:
        """Get the path to the pg0 binary."""
        if self._binary_path is None:
            # Default install location
            return Path.home() / ".hindsight" / "bin" / "pg0"
        return self._binary_path

    def is_installed(self) -> bool:
        """Check if pg0 is available (in PATH or installed)."""
        self._binary_path = _find_pg0_binary()
        return self._binary_path is not None

    async def ensure_installed(self) -> None:
        """
        Ensure pg0 is available.

        First checks PATH, then default location, then downloads if needed.
        """
        if self.is_installed():
            logger.debug(f"pg0 found at {self._binary_path}")
            return

        logger.info("pg0 not found, downloading...")

        # Log platform information
        binary_name = get_platform_binary_name()
        logger.info(f"Detected platform: system={platform.system()}, machine={platform.machine()}")

        # Install to default location
        install_dir = Path.home() / ".hindsight" / "bin"
        install_dir.mkdir(parents=True, exist_ok=True)
        install_path = install_dir / "pg0"

        # Download the binary
        download_url = get_download_url(self.version)
        logger.info(f"Downloading from {download_url}")

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
                response = await client.get(download_url)
                response.raise_for_status()

                # Write binary to disk
                with open(install_path, "wb") as f:
                    f.write(response.content)

                # Make executable on Unix
                if platform.system() != "Windows":
                    st = os.stat(install_path)
                    os.chmod(install_path, st.st_mode | stat.S_IEXEC)

                self._binary_path = install_path
                logger.info(f"Installed pg0 to {install_path}")

        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to download pg0: {e}") from e

    def _run_command(self, *args: str, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a pg0 command synchronously."""
        cmd = [str(self.binary_path), *args]
        return subprocess.run(cmd, capture_output=capture_output, text=True)

    async def _run_command_async(self, *args: str, timeout: int = 120) -> tuple[int, str, str]:
        """Run a pg0 command asynchronously."""
        cmd = [str(self.binary_path), *args]

        def run_sync():
            try:
                result = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                )
                return result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired:
                return 1, "", "Command timed out"

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_sync)

    def _extract_uri_from_output(self, output: str) -> Optional[str]:
        """Extract the PostgreSQL URI from pg0 start output."""
        match = re.search(r"Connection URI:\s*(postgresql://[^\s]+)", output)
        if match:
            return match.group(1)
        return None

    async def start(self, max_retries: int = 3, retry_delay: float = 2.0) -> str:
        """
        Start the PostgreSQL server with retry logic.

        Args:
            max_retries: Maximum number of start attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 2.0)

        Returns:
            The connection URI for the started server.

        Raises:
            RuntimeError: If the server fails to start after all retries.
        """
        if not self.is_installed():
            raise RuntimeError("pg0 is not installed. Call ensure_installed() first.")

        logger.info(f"Starting embedded PostgreSQL (name: {self.name}, port: {self.port})...")

        last_error = None
        for attempt in range(1, max_retries + 1):
            returncode, stdout, stderr = await self._run_command_async(
                "start",
                "--name", self.name,
                "--port", str(self.port),
                "--username", self.username,
                "--password", self.password,
                "--database", self.database,
                timeout=300,
            )

            # Try to extract URI from output
            uri = self._extract_uri_from_output(stdout)
            if uri:
                logger.info(f"PostgreSQL started on port {self.port}")
                return uri

            # Check if pg0 info can find the running instance
            try:
                uri = await self.get_uri()
                logger.info(f"PostgreSQL started on port {self.port}")
                return uri
            except RuntimeError:
                pass

            # Start failed, log and retry
            last_error = stderr or f"pg0 start returned exit code {returncode}"
            if attempt < max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                logger.warning(f"pg0 start attempt {attempt}/{max_retries} failed: {last_error.strip()}")
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.warning(f"pg0 start attempt {attempt}/{max_retries} failed: {last_error.strip()}")

        # All retries exhausted - use constructed URI as fallback
        uri = f"postgresql://{self.username}:{self.password}@localhost:{self.port}/{self.database}"
        logger.warning(f"All pg0 start attempts failed, using constructed URI: {uri}")
        return uri

    async def stop(self) -> None:
        """Stop the PostgreSQL server."""
        if not self.is_installed():
            return

        logger.info(f"Stopping embedded PostgreSQL (name: {self.name})...")

        returncode, stdout, stderr = await self._run_command_async("stop", "--name", self.name)

        if returncode != 0:
            if "not running" in stderr.lower():
                return
            raise RuntimeError(f"Failed to stop PostgreSQL: {stderr}")

        logger.info("Embedded PostgreSQL stopped")

    async def _get_info(self) -> dict:
        """Get info from pg0 using the `info -o json` command."""
        if not self.is_installed():
            raise RuntimeError("pg0 is not installed.")

        returncode, stdout, stderr = await self._run_command_async(
            "info", "--name", self.name, "-o", "json"
        )

        if returncode != 0:
            raise RuntimeError(f"Failed to get PostgreSQL info: {stderr}")

        try:
            return json.loads(stdout.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse pg0 info output: {e}")

    async def get_uri(self) -> str:
        """Get the connection URI for the PostgreSQL server."""
        info = await self._get_info()
        uri = info.get("uri")
        if not uri:
            raise RuntimeError("PostgreSQL server is not running or URI not available")
        return uri

    async def status(self) -> dict:
        """Get the status of the PostgreSQL server."""
        if not self.is_installed():
            return {"installed": False, "running": False}

        try:
            info = await self._get_info()
            return {
                "installed": True,
                "running": info.get("running", False),
                "uri": info.get("uri"),
            }
        except RuntimeError:
            return {"installed": True, "running": False}

    async def is_running(self) -> bool:
        """Check if the PostgreSQL server is currently running."""
        if not self.is_installed():
            return False
        try:
            info = await self._get_info()
            return info.get("running", False)
        except RuntimeError:
            return False

    async def ensure_running(self) -> str:
        """
        Ensure the PostgreSQL server is running.

        Installs if needed, starts if not running.

        Returns:
            The connection URI.
        """
        await self.ensure_installed()

        if await self.is_running():
            return await self.get_uri()

        return await self.start()

    def uninstall(self) -> None:
        """Remove the pg0 binary (only if we installed it)."""
        default_path = Path.home() / ".hindsight" / "bin" / "pg0"
        if default_path.exists():
            default_path.unlink()
            logger.info(f"Removed {default_path}")

    def clear_data(self) -> None:
        """Remove all PostgreSQL data (destructive!)."""
        result = self._run_command("drop", "--name", self.name, "--force")
        if result.returncode == 0:
            logger.info(f"Dropped pg0 instance {self.name}")
        else:
            logger.warning(f"Failed to drop pg0 instance {self.name}: {result.stderr}")


# Convenience functions

_default_instance: Optional[EmbeddedPostgres] = None


def get_embedded_postgres() -> EmbeddedPostgres:
    """Get or create the default EmbeddedPostgres instance."""
    global _default_instance

    if _default_instance is None:
        _default_instance = EmbeddedPostgres()

    return _default_instance


async def start_embedded_postgres() -> str:
    """
    Quick start function for embedded PostgreSQL.

    Downloads, installs, and starts PostgreSQL in one call.

    Returns:
        Connection URI string

    Example:
        db_url = await start_embedded_postgres()
        conn = await asyncpg.connect(db_url)
    """
    pg = get_embedded_postgres()
    return await pg.ensure_running()


async def stop_embedded_postgres() -> None:
    """Stop the default embedded PostgreSQL instance."""
    global _default_instance

    if _default_instance:
        await _default_instance.stop()
