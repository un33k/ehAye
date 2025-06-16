"""Safe file operation utilities."""

import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union, BinaryIO, TextIO

from ..exceptions import ModelError
from ..logging import get_logger

logger = get_logger("utilities.file_ops")


def safe_copy(
    src: Union[str, Path],
    dst: Union[str, Path],
    preserve_metadata: bool = True,
    overwrite: bool = False
) -> Path:
    """Safely copy a file with error handling."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Validate source
    if not src_path.exists():
        raise ModelError(f"Source file does not exist: {src_path}")
    
    if not src_path.is_file():
        raise ModelError(f"Source is not a file: {src_path}")
    
    # Check destination
    if dst_path.exists() and not overwrite:
        raise ModelError(f"Destination already exists: {dst_path}")
    
    # Create destination directory if needed
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if preserve_metadata:
            shutil.copy2(src_path, dst_path)
        else:
            shutil.copy(src_path, dst_path)
        
        logger.debug(f"Copied {src_path} -> {dst_path}")
        return dst_path
        
    except OSError as e:
        raise ModelError(f"Failed to copy file: {e}")


def safe_move(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> Path:
    """Safely move a file with error handling."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Validate source
    if not src_path.exists():
        raise ModelError(f"Source file does not exist: {src_path}")
    
    # Check destination
    if dst_path.exists() and not overwrite:
        raise ModelError(f"Destination already exists: {dst_path}")
    
    # Create destination directory if needed
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.move(str(src_path), str(dst_path))
        logger.debug(f"Moved {src_path} -> {dst_path}")
        return dst_path
        
    except OSError as e:
        raise ModelError(f"Failed to move file: {e}")


def safe_delete(
    path: Union[str, Path],
    ignore_missing: bool = True,
    recursive: bool = False
) -> bool:
    """Safely delete a file or directory."""
    path_obj = Path(path)
    
    if not path_obj.exists():
        if ignore_missing:
            return False
        else:
            raise ModelError(f"Path does not exist: {path_obj}")
    
    try:
        if path_obj.is_file():
            path_obj.unlink()
            logger.debug(f"Deleted file: {path_obj}")
        elif path_obj.is_dir():
            if recursive:
                shutil.rmtree(path_obj)
                logger.debug(f"Deleted directory: {path_obj}")
            else:
                path_obj.rmdir()  # Only works if empty
                logger.debug(f"Deleted empty directory: {path_obj}")
        else:
            raise ModelError(f"Path is neither file nor directory: {path_obj}")
        
        return True
        
    except OSError as e:
        raise ModelError(f"Failed to delete {path_obj}: {e}")


def calculate_checksum(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """Calculate file checksum."""
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise ModelError(f"File does not exist: {path_obj}")
    
    if not path_obj.is_file():
        raise ModelError(f"Path is not a file: {path_obj}")
    
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ModelError(f"Unsupported hash algorithm: {algorithm}")
    
    try:
        with open(path_obj, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        
        checksum = hasher.hexdigest()
        logger.debug(f"Calculated {algorithm} checksum for {path_obj}: {checksum}")
        return checksum
        
    except OSError as e:
        raise ModelError(f"Failed to calculate checksum: {e}")


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """Verify file checksum matches expected value."""
    actual_checksum = calculate_checksum(file_path, algorithm)
    
    if actual_checksum.lower() != expected_checksum.lower():
        raise ModelError(
            f"Checksum mismatch for {file_path}: "
            f"expected {expected_checksum}, got {actual_checksum}"
        )
    
    logger.debug(f"Checksum verified for {file_path}")
    return True


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise ModelError(f"File does not exist: {path_obj}")
    
    if not path_obj.is_file():
        raise ModelError(f"Path is not a file: {path_obj}")
    
    try:
        return path_obj.stat().st_size
    except OSError as e:
        raise ModelError(f"Failed to get file size: {e}")


def get_directory_size(dir_path: Union[str, Path]) -> int:
    """Get total size of directory in bytes."""
    path_obj = Path(dir_path)
    
    if not path_obj.exists():
        raise ModelError(f"Directory does not exist: {path_obj}")
    
    if not path_obj.is_dir():
        raise ModelError(f"Path is not a directory: {path_obj}")
    
    total_size = 0
    try:
        for file_path in path_obj.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    except OSError as e:
        raise ModelError(f"Failed to calculate directory size: {e}")


def create_temp_file(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[Union[str, Path]] = None,
    text: bool = False
) -> Union[BinaryIO, TextIO]:
    """Create a temporary file."""
    try:
        return tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=str(dir) if dir else None,
            mode='w+t' if text else 'w+b',
            delete=False
        )
    except OSError as e:
        raise ModelError(f"Failed to create temporary file: {e}")


def create_temp_directory(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[Union[str, Path]] = None
) -> Path:
    """Create a temporary directory."""
    try:
        temp_dir = tempfile.mkdtemp(
            suffix=suffix,
            prefix=prefix,
            dir=str(dir) if dir else None
        )
        return Path(temp_dir)
    except OSError as e:
        raise ModelError(f"Failed to create temporary directory: {e}")


def atomic_write(
    content: Union[str, bytes],
    file_path: Union[str, Path],
    encoding: str = 'utf-8',
    create_backup: bool = False
) -> Path:
    """Atomically write content to a file."""
    path_obj = Path(file_path)
    
    # Create backup if requested
    backup_path = None
    if create_backup and path_obj.exists():
        backup_path = path_obj.with_suffix(path_obj.suffix + '.backup')
        safe_copy(path_obj, backup_path, overwrite=True)
    
    # Write to temporary file first
    temp_path = path_obj.with_suffix(path_obj.suffix + '.tmp')
    
    try:
        # Create parent directory if needed
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        if isinstance(content, str):
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)
        else:
            with open(temp_path, 'wb') as f:
                f.write(content)
        
        # Atomic move
        temp_path.replace(path_obj)
        logger.debug(f"Atomically wrote to {path_obj}")
        
        # Remove backup if everything succeeded
        if backup_path and backup_path.exists():
            backup_path.unlink()
        
        return path_obj
        
    except Exception as e:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()
        
        # Restore backup if it exists
        if backup_path and backup_path.exists():
            backup_path.replace(path_obj)
        
        raise ModelError(f"Failed to write file atomically: {e}")


def ensure_directory(dir_path: Union[str, Path], mode: int = 0o755) -> Path:
    """Ensure directory exists with proper permissions."""
    path_obj = Path(dir_path)
    
    try:
        path_obj.mkdir(parents=True, exist_ok=True, mode=mode)
        return path_obj
    except OSError as e:
        raise ModelError(f"Failed to create directory {path_obj}: {e}")


def list_files(
    dir_path: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
    include_dirs: bool = False
) -> list[Path]:
    """List files in directory with optional filtering."""
    path_obj = Path(dir_path)
    
    if not path_obj.exists():
        raise ModelError(f"Directory does not exist: {path_obj}")
    
    if not path_obj.is_dir():
        raise ModelError(f"Path is not a directory: {path_obj}")
    
    try:
        if recursive:
            files = path_obj.rglob(pattern)
        else:
            files = path_obj.glob(pattern)
        
        result = []
        for file_path in files:
            if include_dirs or file_path.is_file():
                result.append(file_path)
        
        return sorted(result)
        
    except OSError as e:
        raise ModelError(f"Failed to list files in {path_obj}: {e}")


def compress_file(
    file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    compression: str = "gzip"
) -> Path:
    """Compress a file using specified compression."""
    import gzip
    import bz2
    import lzma
    
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise ModelError(f"File does not exist: {path_obj}")
    
    if output_path is None:
        if compression == "gzip":
            output_path = path_obj.with_suffix(path_obj.suffix + '.gz')
        elif compression == "bzip2":
            output_path = path_obj.with_suffix(path_obj.suffix + '.bz2')
        elif compression == "xz":
            output_path = path_obj.with_suffix(path_obj.suffix + '.xz')
        else:
            raise ModelError(f"Unsupported compression: {compression}")
    
    output_obj = Path(output_path)
    
    try:
        if compression == "gzip":
            opener = gzip.open
        elif compression == "bzip2":
            opener = bz2.open
        elif compression == "xz":
            opener = lzma.open
        else:
            raise ModelError(f"Unsupported compression: {compression}")
        
        with open(path_obj, 'rb') as f_in:
            with opener(output_obj, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.debug(f"Compressed {path_obj} -> {output_obj}")
        return output_obj
        
    except Exception as e:
        raise ModelError(f"Failed to compress file: {e}")