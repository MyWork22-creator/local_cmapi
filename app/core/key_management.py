"""JWT key management utilities."""
import os
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class KeyManager:
    """Utility class for managing JWT signing keys."""
    
    @staticmethod
    def generate_rsa_key_pair(key_size: int = 2048) -> Tuple[str, str]:
        """
        Generate an RSA key pair for JWT signing.
        
        Args:
            key_size: Size of the RSA key (default 2048)
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return private_pem, public_pem
    
    @staticmethod
    def save_key_pair_to_files(
        private_key_pem: str, 
        public_key_pem: str, 
        private_key_path: str = "private_key.pem",
        public_key_path: str = "public_key.pem"
    ) -> None:
        """
        Save RSA key pair to files.
        
        Args:
            private_key_pem: Private key in PEM format
            public_key_pem: Public key in PEM format
            private_key_path: Path to save private key
            public_key_path: Path to save public key
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(private_key_path) if os.path.dirname(private_key_path) else '.', exist_ok=True)
        os.makedirs(os.path.dirname(public_key_path) if os.path.dirname(public_key_path) else '.', exist_ok=True)
        
        # Save private key
        with open(private_key_path, 'w') as f:
            f.write(private_key_pem)
        
        # Set restrictive permissions on private key
        os.chmod(private_key_path, 0o600)
        
        # Save public key
        with open(public_key_path, 'w') as f:
            f.write(public_key_pem)
        
        # Set readable permissions on public key
        os.chmod(public_key_path, 0o644)
    
    @staticmethod
    def load_key_from_file(key_path: str) -> str:
        """
        Load a key from file.
        
        Args:
            key_path: Path to the key file
            
        Returns:
            Key content as string
        """
        try:
            with open(key_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Key file not found: {key_path}")
        except Exception as e:
            raise Exception(f"Error loading key from {key_path}: {e}")
    
    @staticmethod
    def validate_rsa_key_pair(private_key_pem: str, public_key_pem: str) -> bool:
        """
        Validate that a private and public key pair match.
        
        Args:
            private_key_pem: Private key in PEM format
            public_key_pem: Public key in PEM format
            
        Returns:
            True if keys match, False otherwise
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            
            # Load keys
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Test signing and verification
            test_message = b"test message for key validation"
            
            # Sign with private key
            signature = private_key.sign(
                test_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Verify with public key
            public_key.verify(
                signature,
                test_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def generate_development_keys() -> None:
        """Generate RSA key pair for development use."""
        print("Generating RSA key pair for development...")
        
        private_key, public_key = KeyManager.generate_rsa_key_pair()
        
        # Save to keys directory
        keys_dir = "keys"
        private_path = os.path.join(keys_dir, "private_key.pem")
        public_path = os.path.join(keys_dir, "public_key.pem")
        
        KeyManager.save_key_pair_to_files(
            private_key, 
            public_key, 
            private_path, 
            public_path
        )
        
        print(f"✅ RSA key pair generated successfully!")
        print(f"   Private key: {private_path}")
        print(f"   Public key: {public_path}")
        print("\n🔧 To use RS256 algorithm, set these environment variables:")
        print(f"   RSA_PRIVATE_KEY_PATH={private_path}")
        print(f"   RSA_PUBLIC_KEY_PATH={public_path}")
        print(f"   JWT_ALGORITHM=RS256")
        print("\n⚠️  Keep the private key secure and never commit it to version control!")


def generate_keys_command():
    """Command-line utility to generate keys."""
    KeyManager.generate_development_keys()


if __name__ == "__main__":
    generate_keys_command()
