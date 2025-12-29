"""
Encryption utilities for sensitive data at rest.
Uses Fernet (AES-256) for symmetric encryption.
"""
import os
import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    InvalidToken = None


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class DataEncryptor:
    """
    Handles encryption and decryption of sensitive data.
    Uses Fernet (AES-256-CBC) with PBKDF2 key derivation.
    """
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        Initialize encryptor.
        
        Args:
            key_file: Path to file containing encryption key (creates if not exists)
        """
        if not CRYPTO_AVAILABLE:
            raise EncryptionError(
                "Cryptography library not available. "
                "Install with: pip install cryptography"
            )
        
        self.key_file = key_file or Path.home() / ".oa_encryption_key"
        self.cipher = self._get_or_create_cipher()
    
    def _generate_key(self) -> bytes:
        """
        Generate a new encryption key using secure random.
        
        Returns:
            32-byte encryption key
        """
        # Use secrets module for cryptographically strong random
        key = secrets.token_bytes(32)
        return key
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: User password
            salt: Salt for key derivation
            
        Returns:
            Derived key
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP 2023 recommendation
        )
        return kdf.derive(password.encode())
    
    def _get_or_create_cipher(self) -> Fernet:
        """
        Get existing or create new cipher.
        
        Returns:
            Fernet cipher instance
        """
        if self.key_file.exists():
            # Load existing key
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                return Fernet(key)
            except Exception as e:
                raise EncryptionError(f"Failed to load encryption key: {e}")
        else:
            # Generate and save new key
            key = Fernet.generate_key()
            
            # Ensure parent directory exists
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save key with restrictive permissions
            try:
                # Write key
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                
                # Set restrictive permissions (owner read/write only)
                os.chmod(self.key_file, 0o600)
                
                return Fernet(key)
            except Exception as e:
                # Clean up partial file
                if self.key_file.exists():
                    self.key_file.unlink()
                raise EncryptionError(f"Failed to create encryption key: {e}")
    
    def encrypt_string(self, plaintext: str) -> bytes:
        """
        Encrypt a string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted bytes
        """
        try:
            return self.cipher.encrypt(plaintext.encode('utf-8'))
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt_string(self, ciphertext: bytes) -> str:
        """
        Decrypt to string.
        
        Args:
            ciphertext: Encrypted bytes
            
        Returns:
            Decrypted string
        """
        try:
            plaintext_bytes = self.cipher.decrypt(ciphertext)
            return plaintext_bytes.decode('utf-8')
        except InvalidToken:
            raise EncryptionError("Decryption failed: invalid key or corrupted data")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> bytes:
        """
        Encrypt a dictionary.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted bytes
        """
        json_str = json.dumps(data)
        return self.encrypt_string(json_str)
    
    def decrypt_dict(self, ciphertext: bytes) -> Dict[str, Any]:
        """
        Decrypt to dictionary.
        
        Args:
            ciphertext: Encrypted bytes
            
        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt_string(ciphertext)
        return json.loads(json_str)
    
    def encrypt_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted file (default: input_path + '.encrypted')
            
        Returns:
            Path to encrypted file
        """
        if not input_path.exists():
            raise EncryptionError(f"Input file not found: {input_path}")
        
        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + '.encrypted')
        
        try:
            # Read plaintext
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            # Encrypt
            ciphertext = self.cipher.encrypt(plaintext)
            
            # Write ciphertext
            with open(output_path, 'wb') as f:
                f.write(ciphertext)
            
            # Set restrictive permissions
            os.chmod(output_path, 0o600)
            
            return output_path
        except Exception as e:
            raise EncryptionError(f"File encryption failed: {e}")
    
    def decrypt_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted file (default: remove '.encrypted')
            
        Returns:
            Path to decrypted file
        """
        if not input_path.exists():
            raise EncryptionError(f"Input file not found: {input_path}")
        
        if output_path is None:
            if input_path.suffix == '.encrypted':
                output_path = input_path.with_suffix('')
            else:
                output_path = input_path.with_suffix('.decrypted')
        
        try:
            # Read ciphertext
            with open(input_path, 'rb') as f:
                ciphertext = f.read()
            
            # Decrypt
            plaintext = self.cipher.decrypt(ciphertext)
            
            # Write plaintext
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            return output_path
        except InvalidToken:
            raise EncryptionError("Decryption failed: invalid key or corrupted file")
        except Exception as e:
            raise EncryptionError(f"File decryption failed: {e}")


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded token string
    """
    return secrets.token_hex(length)


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure random password.
    
    Args:
        length: Password length
        
    Returns:
        Random password
    """
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Global encryptor instance (lazy initialization)
_global_encryptor: Optional[DataEncryptor] = None


def get_encryptor(key_file: Optional[Path] = None) -> DataEncryptor:
    """
    Get global encryptor instance.
    
    Args:
        key_file: Optional path to key file
        
    Returns:
        DataEncryptor instance
    """
    global _global_encryptor
    
    if _global_encryptor is None:
        if not CRYPTO_AVAILABLE:
            raise EncryptionError(
                "Cryptography library not available. "
                "Install with: pip install cryptography"
            )
        _global_encryptor = DataEncryptor(key_file)
    
    return _global_encryptor

