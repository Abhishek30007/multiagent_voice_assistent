import pytest
from app.core.security import encrypt_token, decrypt_token


def test_token_encryption_and_decryption():
    secret_token = "ya29.a0AfH6SMAexample_google_oauth_access_token_12345"
    encrypted = encrypt_token(secret_token)
    
    assert encrypted is not None
    assert encrypted != secret_token
    assert len(encrypted) > len(secret_token)
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == secret_token


def test_token_encryption_handles_none():
    assert encrypt_token(None) is None
    assert decrypt_token(None) is None


def test_token_decryption_invalid_data():
    with pytest.raises(ValueError):
        decrypt_token("invalid-malformed-cipher-text")
