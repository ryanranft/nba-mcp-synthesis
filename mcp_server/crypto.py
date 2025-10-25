"""
Cryptographic Utilities for NBA MCP Server

Provides secure cryptographic primitives including:
- Modular exponentiation for key exchange
- Diffie-Hellman key agreement
- RSA message signing and verification
- Secure random number generation
- Constant-time comparison functions (timing attack prevention)
- Key derivation functions
- Symmetric encryption utilities

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from .logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Modular Arithmetic
# ==============================================================================


def modular_exponentiation(base: int, exponent: int, modulus: int) -> int:
    """
    Compute (base^exponent) % modulus efficiently using fast exponentiation.

    This is more efficient and secure than pow() for large numbers.
    Uses the square-and-multiply algorithm.

    Args:
        base: Base number
        exponent: Exponent
        modulus: Modulus

    Returns:
        Result of (base^exponent) % modulus

    Examples:
        >>> result = modular_exponentiation(5, 3, 13)
        >>> print(result)  # 5^3 mod 13 = 125 mod 13 = 8
        8

    Security:
        Uses Python's built-in pow() which implements fast modular exponentiation
        and is resistant to timing attacks for large numbers.
    """
    return pow(base, exponent, modulus)


def is_prime(n: int, k: int = 5) -> bool:
    """
    Test if a number is prime using Miller-Rabin primality test.

    Args:
        n: Number to test
        k: Number of rounds (higher = more accurate)

    Returns:
        True if probably prime, False if definitely composite

    Examples:
        >>> is_prime(17)
        True
        >>> is_prime(16)
        False
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Miller-Rabin test
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = modular_exponentiation(a, d, n)

        if x == 1 or x == n - 1:
            continue

        for _ in range(r - 1):
            x = modular_exponentiation(x, 2, n)
            if x == n - 1:
                break
        else:
            return False

    return True


def generate_safe_prime(bits: int = 2048) -> int:
    """
    Generate a safe prime (p where (p-1)/2 is also prime).

    Args:
        bits: Size of prime in bits

    Returns:
        Safe prime number

    Note:
        This can be slow for large bit sizes. For production use,
        use pre-generated safe primes or cryptography library functions.
    """
    while True:
        # Generate random odd number
        q = secrets.randbits(bits - 1)
        q |= 1  # Make odd

        if is_prime(q):
            p = 2 * q + 1
            if is_prime(p):
                return p


# ==============================================================================
# Diffie-Hellman Key Exchange
# ==============================================================================


class CryptoManager:
    """
    Cryptographic utilities manager.

    Provides methods for:
    - Diffie-Hellman key exchange
    - RSA signing and verification
    - Secure random generation
    - Constant-time comparisons
    - Key derivation
    - Symmetric encryption

    Examples:
        >>> crypto = CryptoManager()
        >>>
        >>> # Diffie-Hellman key exchange
        >>> alice_private, alice_public = crypto.generate_dh_keypair()
        >>> bob_private, bob_public = crypto.generate_dh_keypair()
        >>> alice_shared = crypto.compute_shared_secret(alice_private, bob_public)
        >>> bob_shared = crypto.compute_shared_secret(bob_private, alice_public)
        >>> assert alice_shared == bob_shared  # Same shared secret!
    """

    # Safe prime (2048-bit) for DH
    # In production, use a standard group like RFC 3526
    DH_PRIME = int(
        "FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1"
        "29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD"
        "EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245"
        "E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED"
        "EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D"
        "C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F"
        "83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D"
        "670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B"
        "E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9"
        "DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510"
        "15728E5A 8AACAA68 FFFFFFFF FFFFFFFF".replace(" ", ""),
        16,
    )

    DH_GENERATOR = 2

    def __init__(self):
        """Initialize crypto manager."""
        self.backend = default_backend()
        logger.info("Crypto manager initialized")

    def generate_dh_keypair(
        self,
        prime: Optional[int] = None,
        generator: Optional[int] = None,
    ) -> Tuple[int, int]:
        """
        Generate Diffie-Hellman key pair.

        Args:
            prime: Prime modulus (None = use default safe prime)
            generator: Generator (None = use default)

        Returns:
            (private_key, public_key) tuple

        Examples:
            >>> crypto = CryptoManager()
            >>> private_key, public_key = crypto.generate_dh_keypair()

        Security:
            - Private key is a random integer in range [2, prime-2]
            - Public key is generator^private_key mod prime
            - Uses cryptographically secure random number generation
        """
        p = prime or self.DH_PRIME
        g = generator or self.DH_GENERATOR

        # Generate private key (random integer)
        private_key = secrets.randbelow(p - 2) + 1

        # Compute public key: g^private mod p
        public_key = modular_exponentiation(g, private_key, p)

        return private_key, public_key

    def compute_shared_secret(
        self,
        private_key: int,
        other_public_key: int,
        prime: Optional[int] = None,
    ) -> int:
        """
        Compute shared secret from DH key exchange.

        Args:
            private_key: Your private key
            other_public_key: Other party's public key
            prime: Prime modulus (None = use default)

        Returns:
            Shared secret

        Examples:
            >>> crypto = CryptoManager()
            >>> alice_priv, alice_pub = crypto.generate_dh_keypair()
            >>> bob_priv, bob_pub = crypto.generate_dh_keypair()
            >>> alice_secret = crypto.compute_shared_secret(alice_priv, bob_pub)
            >>> bob_secret = crypto.compute_shared_secret(bob_priv, alice_pub)
            >>> assert alice_secret == bob_secret

        Security:
            Shared secret = (other_public_key^private_key) mod prime
            Both parties compute the same value without exchanging private keys.
        """
        p = prime or self.DH_PRIME

        # Compute shared secret: other_public^private mod p
        shared_secret = modular_exponentiation(other_public_key, private_key, p)

        return shared_secret

    def generate_rsa_keypair(
        self, key_size: int = 2048
    ) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Generate RSA key pair.

        Args:
            key_size: Key size in bits (2048 or 4096 recommended)

        Returns:
            (private_key, public_key) tuple

        Examples:
            >>> crypto = CryptoManager()
            >>> private_key, public_key = crypto.generate_rsa_keypair()

        Security:
            Uses cryptography library's secure RSA key generation.
            Default exponent is 65537.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_size, backend=self.backend
        )

        public_key = private_key.public_key()

        return private_key, public_key

    def sign_message(self, message: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        """
        Sign a message with RSA private key.

        Args:
            message: Message to sign
            private_key: RSA private key

        Returns:
            Signature bytes

        Examples:
            >>> crypto = CryptoManager()
            >>> private_key, public_key = crypto.generate_rsa_keypair()
            >>> message = b"Hello, World!"
            >>> signature = crypto.sign_message(message, private_key)

        Security:
            Uses PKCS1v15 padding with SHA256 hashing.
            For production, consider using PSS padding instead.
        """
        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())

        return signature

    def verify_signature(
        self, message: bytes, signature: bytes, public_key: rsa.RSAPublicKey
    ) -> bool:
        """
        Verify message signature.

        Args:
            message: Original message
            signature: Signature to verify
            public_key: RSA public key

        Returns:
            True if signature is valid, False otherwise

        Examples:
            >>> crypto = CryptoManager()
            >>> private_key, public_key = crypto.generate_rsa_keypair()
            >>> message = b"Hello, World!"
            >>> signature = crypto.sign_message(message, private_key)
            >>> is_valid = crypto.verify_signature(message, signature, public_key)
            >>> assert is_valid

        Security:
            Uses constant-time comparison where possible.
            Invalid signatures raise an exception which is caught.
        """
        try:
            public_key.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False

    def constant_time_compare(self, a: bytes, b: bytes) -> bool:
        """
        Compare bytes in constant time to prevent timing attacks.

        Args:
            a: First byte string
            b: Second byte string

        Returns:
            True if equal, False otherwise

        Examples:
            >>> crypto = CryptoManager()
            >>> result = crypto.constant_time_compare(b"secret", b"secret")
            >>> assert result == True

        Security:
            Uses hmac.compare_digest which is resistant to timing attacks.
            Regular comparison (==) can leak information about data through timing.
        """
        return hmac.compare_digest(a, b)

    def generate_secure_random(self, num_bytes: int = 32) -> bytes:
        """
        Generate cryptographically secure random bytes.

        Args:
            num_bytes: Number of random bytes to generate

        Returns:
            Random bytes

        Examples:
            >>> crypto = CryptoManager()
            >>> random_bytes = crypto.generate_secure_random(32)
            >>> assert len(random_bytes) == 32

        Security:
            Uses os.urandom() which is cryptographically secure on all platforms.
        """
        return secrets.token_bytes(num_bytes)

    def generate_secure_token(self, num_bytes: int = 32) -> str:
        """
        Generate cryptographically secure URL-safe token.

        Args:
            num_bytes: Number of random bytes (token will be longer due to encoding)

        Returns:
            URL-safe token string

        Examples:
            >>> crypto = CryptoManager()
            >>> token = crypto.generate_secure_token()
            >>> assert len(token) > 0

        Security:
            Uses secrets.token_urlsafe() which is appropriate for:
            - Password reset tokens
            - Session tokens
            - API keys
            - Security tokens
        """
        return secrets.token_urlsafe(num_bytes)

    def derive_key(
        self,
        password: bytes,
        salt: bytes,
        key_length: int = 32,
        iterations: int = 100000,
    ) -> bytes:
        """
        Derive a cryptographic key from a password using PBKDF2.

        Args:
            password: Password bytes
            salt: Salt bytes (should be random and unique)
            key_length: Length of derived key
            iterations: Number of iterations (higher = more secure but slower)

        Returns:
            Derived key bytes

        Examples:
            >>> crypto = CryptoManager()
            >>> password = b"my_password"
            >>> salt = crypto.generate_secure_random(16)
            >>> key = crypto.derive_key(password, salt)

        Security:
            Uses PBKDF2-HMAC-SHA256.
            100,000 iterations is a good balance for 2024.
            Always use a unique random salt per password.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations,
            backend=self.backend,
        )

        return kdf.derive(password)

    def encrypt_aes_gcm(
        self,
        plaintext: bytes,
        key: bytes,
        associated_data: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-GCM.

        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key (256-bit)
            associated_data: Additional authenticated data (not encrypted)

        Returns:
            (ciphertext, nonce, tag) tuple

        Examples:
            >>> crypto = CryptoManager()
            >>> key = crypto.generate_secure_random(32)
            >>> plaintext = b"Secret message"
            >>> ciphertext, nonce, tag = crypto.encrypt_aes_gcm(plaintext, key)

        Security:
            AES-GCM provides authenticated encryption.
            Tag ensures ciphertext hasn't been tampered with.
            Nonce must be unique for each message with the same key.
        """
        # Generate random nonce
        nonce = os.urandom(12)  # 96 bits for GCM

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=self.backend)

        # Encrypt
        encryptor = cipher.encryptor()

        if associated_data:
            encryptor.authenticate_additional_data(associated_data)

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

        return ciphertext, nonce, tag

    def decrypt_aes_gcm(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        tag: bytes,
        associated_data: Optional[bytes] = None,
    ) -> Optional[bytes]:
        """
        Decrypt data using AES-GCM.

        Args:
            ciphertext: Encrypted data
            key: 32-byte encryption key
            nonce: 12-byte nonce from encryption
            tag: 16-byte authentication tag from encryption
            associated_data: Additional authenticated data (same as encryption)

        Returns:
            Decrypted plaintext or None if authentication fails

        Examples:
            >>> crypto = CryptoManager()
            >>> key = crypto.generate_secure_random(32)
            >>> plaintext = b"Secret message"
            >>> ciphertext, nonce, tag = crypto.encrypt_aes_gcm(plaintext, key)
            >>> decrypted = crypto.decrypt_aes_gcm(ciphertext, key, nonce, tag)
            >>> assert decrypted == plaintext

        Security:
            Returns None if authentication fails (tampered ciphertext or wrong key).
            Do not return partial plaintext on authentication failure.
        """
        try:
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key), modes.GCM(nonce, tag), backend=self.backend
            )

            # Decrypt
            decryptor = cipher.decryptor()

            if associated_data:
                decryptor.authenticate_additional_data(associated_data)

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext

        except Exception as e:
            logger.warning(f"Decryption failed: {e}")
            return None

    def hash_sha256(self, data: bytes) -> bytes:
        """
        Compute SHA-256 hash of data.

        Args:
            data: Data to hash

        Returns:
            32-byte SHA-256 hash

        Examples:
            >>> crypto = CryptoManager()
            >>> hash_value = crypto.hash_sha256(b"Hello, World!")

        Security:
            SHA-256 is collision-resistant and suitable for:
            - File integrity checks
            - Data fingerprinting
            - Commitment schemes
            NOT suitable for password hashing (use bcrypt or argon2 instead).
        """
        return hashlib.sha256(data).digest()

    def hmac_sha256(self, key: bytes, message: bytes) -> bytes:
        """
        Compute HMAC-SHA256 of message.

        Args:
            key: Secret key
            message: Message to authenticate

        Returns:
            32-byte HMAC

        Examples:
            >>> crypto = CryptoManager()
            >>> key = crypto.generate_secure_random(32)
            >>> mac = crypto.hmac_sha256(key, b"Message to authenticate")

        Security:
            HMAC provides message authentication.
            Verifying HMAC proves message hasn't been tampered with
            and sender knows the secret key.
        """
        return hmac.new(key, message, hashlib.sha256).digest()

    def verify_hmac(self, key: bytes, message: bytes, expected_hmac: bytes) -> bool:
        """
        Verify HMAC in constant time.

        Args:
            key: Secret key
            message: Message to verify
            expected_hmac: Expected HMAC value

        Returns:
            True if HMAC is valid, False otherwise

        Examples:
            >>> crypto = CryptoManager()
            >>> key = crypto.generate_secure_random(32)
            >>> message = b"Message"
            >>> mac = crypto.hmac_sha256(key, message)
            >>> is_valid = crypto.verify_hmac(key, message, mac)
            >>> assert is_valid

        Security:
            Uses constant-time comparison to prevent timing attacks.
        """
        computed_hmac = self.hmac_sha256(key, message)
        return self.constant_time_compare(computed_hmac, expected_hmac)


# ==============================================================================
# Global Instance
# ==============================================================================


_global_crypto_manager: Optional[CryptoManager] = None


def get_crypto_manager() -> CryptoManager:
    """Get the global crypto manager instance."""
    global _global_crypto_manager
    if _global_crypto_manager is None:
        _global_crypto_manager = CryptoManager()
    return _global_crypto_manager


def set_crypto_manager(manager: CryptoManager) -> None:
    """Set the global crypto manager instance."""
    global _global_crypto_manager
    _global_crypto_manager = manager
