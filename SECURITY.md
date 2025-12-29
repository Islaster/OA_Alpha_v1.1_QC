# Security Guidelines - OA Orientation Automator

## 🔒 Security Overview

This project follows **2025 "Secure-by-Default" standards** with comprehensive security hardening across all modules.

## 🛡️ Security Features Implemented

### 1. Secrets Management

#### ✅ No Hardcoded Secrets
- **All sensitive data** (API keys, tokens, passwords) are loaded from environment variables
- Config files contain **NO secrets** - only empty placeholders
- Python-dotenv support for local `.env` files

#### Configuration Priority
1. **Environment variables** (highest priority)
2. **`.env` file** (local development)
3. **`config.json`** (structure only, no secrets)
4. **Defaults** (lowest priority)

#### Usage

```bash
# Copy template
cp .env.example .env

# Edit .env with your secrets
nano .env

# Never commit .env!
git add .env  # ❌ BLOCKED by .gitignore
```

**Environment Variables:**
```bash
OA_AI_API_KEY=your-api-key-here
OA_DEBUG=false
OA_LOG_LEVEL=INFO
```

### 2. Input Validation & Sanitization

#### Allowlist Approach
All external inputs are validated using **strict allowlists**:

```python
from src.security.validators import (
    validate_3d_file_path,
    validate_object_name,
    validate_rotation_tuple
)

# File paths
validated_path = validate_3d_file_path("model.obj", must_exist=True)

# Object names
safe_name = validate_object_name(user_input)  # Removes dangerous chars

# Rotations
safe_rotation = validate_rotation_tuple((90, 0, 45))
```

#### What's Validated
- ✅ **File paths**: Extension, length, path traversal, null bytes
- ✅ **Object names**: Length, character allowlist
- ✅ **Rotations**: Type, bounds checking
- ✅ **Command arguments**: Injection pattern detection
- ✅ **Log messages**: XSS prevention, newline sanitization

#### Maximum Lengths
- File paths: 4,096 characters
- Object names: 255 characters
- Type names: 100 characters
- Log messages: 10,000 characters

### 3. Command Injection Prevention

#### ❌ Never Use
```python
# DANGEROUS - DO NOT USE
os.system("blender --background " + user_file)  # ❌ Command injection!
subprocess.run(cmd, shell=True)                 # ❌ Shell injection!
```

#### ✅ Always Use
```python
# SECURE - array-based subprocess
cmd = [
    blender_path,
    "--background",
    "--python", script_path,
    "--", input_file
]

# Validate arguments
from src.security.validators import validate_command_args
safe_cmd = validate_command_args(cmd)

# Run without shell
subprocess.run(safe_cmd, shell=False, timeout=600)
```

**All subprocess calls** in the project use the secure array-based approach.

### 4. Data Encryption

#### Sensitive Data at Rest
All sensitive local data is encrypted using **AES-256 (Fernet)**:

```python
from src.security.encryption import get_encryptor

encryptor = get_encryptor()

# Encrypt string
ciphertext = encryptor.encrypt_string("sensitive data")

# Decrypt string
plaintext = encryptor.decrypt_string(ciphertext)

# Encrypt file
encryptor.encrypt_file("data.json", "data.json.encrypted")
```

#### Key Management
- Encryption keys stored in `~/.oa_encryption_key`
- **600 permissions** (owner read/write only)
- Uses `secrets` module for cryptographically secure random generation
- PBKDF2 key derivation with 480,000 iterations (OWASP 2023)

#### What's Encrypted
- Learned rotation data (optional)
- Ground detection patterns (optional)
- Any sensitive configuration data

### 5. Secure Random Generation

#### ❌ Never Use
```python
import random
token = random.randint(0, 1000000)  # ❌ Predictable!
```

#### ✅ Always Use
```python
import secrets

# Secure random token
token = secrets.token_hex(32)

# Secure random password
password = secrets.token_urlsafe(16)

# Secure random choice
item = secrets.choice(items)
```

**All random generation** in the project uses the `secrets` module.

### 6. Error Handling & Information Leakage Prevention

#### Generic User Messages
```python
from src.security.error_handler import SecureError, secure_function

@secure_function(error_code='processing_error')
def process_file(filepath):
    # If error occurs, user sees:
    # "An error occurred during processing. Please try again."
    
    # But detailed error is logged securely:
    # [2025-01-15 10:30:45] ERROR: [processing_error] FileNotFoundError: /path/to/file
    ...
```

#### What Users See
- ❌ **NOT**: `FileNotFoundError: /Users/admin/secret/data.json`
- ✅ **YES**: `The requested file could not be found.`

#### What Gets Logged
- Full exception details (sanitized)
- Stack traces (sanitized paths)
- Timestamps
- Context information

#### Setup
```python
from src.security.error_handler import setup_global_error_handler

# Install global handler
setup_global_error_handler(log_file="secure_errors.log")

# All unhandled exceptions are now caught and handled securely
```

### 7. Dangerous Functions Removed

#### Audit Results
✅ **No usage of dangerous functions:**
- `eval()` - NOT USED
- `exec()` - NOT USED
- `pickle.load()` - NOT USED
- `os.system()` - NOT USED
- `shell=True` - NOT USED

#### Safe Alternatives
- ✅ `json.loads()` for data exchange
- ✅ `ast.literal_eval()` for Python literals
- ✅ Array-based `subprocess.run()` for external commands

## 🔐 Security Best Practices

### For Users

1. **Never Share Your `.env` File**
   - Contains your API keys
   - Keep it secret, keep it safe

2. **Use Strong Encryption**
   ```bash
   # Install cryptography library
   pip install cryptography
   ```

3. **Check File Permissions**
   ```bash
   # Verify restrictive permissions
   ls -la ~/.oa_encryption_key
   # Should show: -rw------- (600)
   ```

4. **Review Logs Regularly**
   - Check `processing_log.txt` for anomalies
   - Logs are sanitized but still sensitive

5. **Keep Software Updated**
   ```bash
   pip install --upgrade -r requirements-security.txt
   ```

### For Developers

1. **Always Validate Input**
   ```python
   from src.security.validators import validate_file_path
   
   # BEFORE using any external input
   safe_path = validate_file_path(user_input, must_exist=True)
   ```

2. **Use Secure Functions**
   ```python
   from src.security.error_handler import secure_function
   
   @secure_function(error_code='my_error')
   def my_function(data):
       # Automatically catches and handles errors securely
       ...
   ```

3. **Never Log Secrets**
   ```python
   # ❌ WRONG
   logger.info(f"API key: {api_key}")
   
   # ✅ CORRECT
   logger.info("API key loaded from environment")
   ```

4. **Sanitize All Logs**
   ```python
   from src.security.validators import sanitize_log_message
   
   safe_msg = sanitize_log_message(user_input)
   logger.info(safe_msg)
   ```

5. **Use Timeouts**
   ```python
   # Always set timeouts on external operations
   subprocess.run(cmd, timeout=600)
   requests.get(url, timeout=30)
   ```

6. **Audit Dependencies**
   ```bash
   # Check for known vulnerabilities
   pip install safety
   safety check
   ```

## 🚨 Security Checklist

### Before Deployment

- [ ] All secrets in `.env`, not in code
- [ ] `.env` file in `.gitignore`
- [ ] No hardcoded API keys in `config.json`
- [ ] All file paths validated
- [ ] All user inputs sanitized
- [ ] No `shell=True` in subprocess calls
- [ ] Error messages don't leak information
- [ ] Logs don't contain secrets
- [ ] Encryption enabled for sensitive data
- [ ] File permissions set correctly (600 for keys)
- [ ] Dependencies updated
- [ ] Security audit passed

### Regular Maintenance

- [ ] Update dependencies monthly
- [ ] Review logs weekly
- [ ] Rotate encryption keys annually
- [ ] Audit access patterns
- [ ] Test backup and recovery

## 📚 Security Modules Reference

### `src/security/validators.py`
Input validation and sanitization
- File path validation
- Object name validation
- Command argument validation
- Log message sanitization

### `src/security/encryption.py`
Data encryption at rest
- AES-256 (Fernet) encryption
- Secure key management
- File encryption/decryption
- Dictionary encryption/decryption

### `src/security/secure_config.py`
Configuration management
- Environment variable support
- `.env` file loading
- Secret detection and warnings
- Priority-based config merging

### `src/security/error_handler.py`
Secure error handling
- Information leakage prevention
- User-friendly error messages
- Detailed secure logging
- Global exception handling

## 🔍 Security Audit Trail

### What's Logged
- File access attempts
- Processing operations
- Error conditions
- Security validations
- Configuration changes

### Log Format
```
2025-01-15 10:30:45 - security - INFO - API key loaded from environment
2025-01-15 10:30:46 - security - WARNING - Suspicious pattern detected in input
2025-01-15 10:30:47 - security - ERROR - [file_read_error] Validation failed: ...
```

### Log Locations
- `processing_log.txt` - General operations
- `debug_log.txt` - Detailed debugging (if enabled)
- `secure_errors.log` - Security-specific events

## 🆘 Security Incident Response

### If You Suspect a Breach

1. **Stop Processing**
   - Terminate all running operations
   - Disconnect from network if necessary

2. **Check Logs**
   ```bash
   grep -i "error\|warning\|suspicious" processing_log.txt
   ```

3. **Rotate Keys**
   ```bash
   # Delete old encryption key
   rm ~/.oa_encryption_key
   
   # Revoke API keys
   # (do this in your API provider dashboard)
   
   # Generate new .env
   cp .env.example .env
   # Fill with NEW keys
   ```

4. **Update Software**
   ```bash
   git pull
   pip install --upgrade -r requirements-security.txt
   ```

5. **Report**
   - Document what happened
   - Contact maintainers if needed
   - Review security practices

## 📞 Security Contact

For security vulnerabilities or concerns:
- **DO NOT** open public GitHub issues
- Review security practices before reporting
- Include minimal reproducible example

## 📖 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security.html)
- [Cryptography Documentation](https://cryptography.io/)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)

---

**Security is everyone's responsibility. Stay vigilant!** 🛡️

