# Security Quick Reference

## 🚀 Quick Start

### 1. Setup (First Time)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your secrets
nano .env  # Add your API keys here

# 3. Install security dependencies
pip install -r requirements-security.txt

# 4. Verify .gitignore (prevents committing secrets)
cat .gitignore | grep ".env"  # Should show .env is ignored
```

### 2. Usage in Code

```python
# Import security modules
from src.security.secure_config import get_secure_config
from src.security.validators import validate_3d_file_path, validate_object_name
from src.security.encryption import get_encryptor
from src.security.error_handler import secure_function

# Load config (with secrets from .env)
config = get_secure_config()
api_key = config.get('ground_detection.ai_api_key')

# Validate inputs
safe_path = validate_3d_file_path(user_input)
safe_name = validate_object_name(object_name)

# Encrypt sensitive data
encryptor = get_encryptor()
encrypted = encryptor.encrypt_string("sensitive")

# Handle errors securely
@secure_function(error_code='my_error')
def my_function():
    # Automatic error handling
    pass
```

## 📋 Common Tasks

### Add a New Secret

**1. Add to `.env`:**
```bash
OA_MY_API_KEY=your-secret-here
```

**2. Load in code:**
```python
config = get_secure_config()
my_key = config.get('my_api_key')  # Loaded from OA_MY_API_KEY env var
```

**3. Document in `.env.example`:**
```bash
# My API Key (get from: https://example.com)
OA_MY_API_KEY=
```

### Validate User Input

```python
from src.security.validators import validate_file_path, validate_object_name

# File paths
try:
    safe_path = validate_file_path(
        user_input,
        purpose="input file",
        must_exist=True,
        allowed_extensions={'.obj', '.fbx'}
    )
    # Use safe_path
except ValidationError as e:
    print(f"Invalid input: {e}")

# Object names
safe_name = validate_object_name(user_input)  # Auto-sanitizes
```

### Encrypt Sensitive Files

```python
from src.security.encryption import get_encryptor

encryptor = get_encryptor()

# Encrypt
encryptor.encrypt_file("data.json", "data.json.encrypted")

# Decrypt when needed
encryptor.decrypt_file("data.json.encrypted", "data.json")
```

### Handle Errors Securely

```python
from src.security.error_handler import secure_function, SecureError

# Option 1: Decorator (automatic)
@secure_function(error_code='processing_error')
def process_file(path):
    # Errors handled automatically
    # User sees: "An error occurred during processing"
    # Log shows: Full details
    ...

# Option 2: Manual
try:
    risky_operation()
except Exception as e:
    raise SecureError(
        "User-friendly message",
        f"Internal: {e}",
        'error_code'
    )
```

## 🔒 Security Rules

### DO ✅

```python
# ✅ Load secrets from environment
config = get_secure_config()
api_key = config.get('ground_detection.ai_api_key')

# ✅ Validate all inputs
safe_path = validate_file_path(user_input)

# ✅ Use array-based subprocess
subprocess.run([cmd, arg1, arg2], shell=False, timeout=600)

# ✅ Use secrets for random
import secrets
token = secrets.token_hex(32)

# ✅ Generic error messages to users
raise SecureError("Processing failed", f"Internal: {details}")

# ✅ Sanitize log messages
from src.security.validators import sanitize_log_message
safe_msg = sanitize_log_message(user_input)
logger.info(safe_msg)
```

### DON'T ❌

```python
# ❌ Hardcode secrets
api_key = "sk-1234567890"  # NEVER!

# ❌ Trust user input
with open(user_input, 'r'):  # Validate first!

# ❌ Use shell=True
subprocess.run(cmd, shell=True)  # Command injection risk!

# ❌ Use random for security
import random
token = random.randint(0, 1000)  # Predictable!

# ❌ Expose internal errors
raise Exception(f"Error at /Users/admin/secret/file.py")  # Info leak!

# ❌ Log secrets
logger.info(f"API key: {api_key}")  # Secret exposed!

# ❌ Use eval/exec/pickle
eval(user_input)  # Code injection!
exec(code)        # Code injection!
pickle.load(f)    # Arbitrary code execution!
```

## 📝 Checklist Before Commit

```bash
# Run this before git commit:

# 1. Check for secrets in code
grep -r "sk-" src/  # Should find nothing
grep -r "api_key.*=" src/ | grep -v "api_key.*=''"  # Should be empty

# 2. Verify .env not tracked
git status | grep ".env"  # Should not appear

# 3. Check .gitignore
cat .gitignore | grep ".env"  # Should be present

# 4. Validate imports
grep -r "from src.security" src/ | wc -l  # Should be > 0

# 5. No dangerous functions
grep -r "eval(" src/ # Should be empty
grep -r "exec(" src/ | grep -v "app.exec()"  # Should be empty (Qt ok)
grep -r "pickle.load" src/  # Should be empty

# 6. No shell=True
grep -r "shell=True" src/  # Should be empty
```

## 🆘 Troubleshooting

### "Cryptography library not available"

```bash
pip install cryptography
```

### "Python-dotenv not available"

```bash
pip install python-dotenv
```

### "ValidationError: Invalid file path"

```python
# Check:
# 1. File exists?
# 2. Extension allowed?
# 3. Path length < 4096?
# 4. No null bytes?

# Debug:
try:
    path = validate_file_path(input)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### "API key not found"

```bash
# 1. Check .env file exists
ls -la .env

# 2. Check variable name
cat .env | grep OA_AI_API_KEY

# 3. Restart application (reload .env)

# 4. Check environment
python -c "import os; print(os.getenv('OA_AI_API_KEY'))"
```

### "Permission denied on encryption key"

```bash
# Fix permissions
chmod 600 ~/.oa_encryption_key

# Verify
ls -la ~/.oa_encryption_key
# Should show: -rw-------
```

## 📚 Full Documentation

- **Comprehensive Guide**: `SECURITY.md`
- **Implementation Details**: `SECURITY_IMPLEMENTATION_SUMMARY.md`
- **Quick Reference**: This file

## 🔗 Key Imports

```python
# Configuration
from src.security.secure_config import get_secure_config, SecureConfig

# Validation
from src.security.validators import (
    validate_file_path,
    validate_3d_file_path,
    validate_config_file_path,
    validate_object_name,
    validate_object_type,
    validate_rotation_tuple,
    validate_command_args,
    sanitize_log_message,
    ValidationError
)

# Encryption
from src.security.encryption import (
    get_encryptor,
    DataEncryptor,
    generate_secure_token,
    generate_secure_password,
    EncryptionError
)

# Error Handling
from src.security.error_handler import (
    secure_function,
    SecureError,
    setup_global_error_handler,
    get_error_handler,
    log_sensitive_operation
)
```

## 💡 Pro Tips

1. **Always use `get_secure_config()`** instead of direct json.load
2. **Validate at boundaries** (GUI input, CLI args, file reads)
3. **Use decorators** for consistent error handling
4. **Encrypt optional** but recommended for sensitive data
5. **Review logs** regularly for security events
6. **Update dependencies** monthly: `pip install --upgrade -r requirements-security.txt`

---

**Quick reference for secure development. See SECURITY.md for details.** 🛡️

