# Security Implementation

## Overview
This document explains the security measures implemented for the Portfolio Backend API.

## Protected Endpoints

### DELETE `/api/contacts`
- **Status**: 🔒 Protected with API Key
- **Requirement**: Must include `X-API-Key` header with valid API key
- **Purpose**: Prevent unauthorized deletion of contact messages
- **Action**: Deletes one or more contact records (dangerous operation)

### GET `/api/contacts`
- **Status**: 🔒 Protected with API Key
- **Requirement**: Must include `X-API-Key` header with valid API key
- **Purpose**: Prevent unauthorized access to contact data (may contain sensitive user information)
- **Action**: Retrieves paginated contact records

### POST `/api/contact`
- **Status**: 🟢 Public (No authentication required)
- **Purpose**: Allow visitors to submit contact forms
- **Note**: CORS protection is in place to restrict cross-origin requests

---

## How to Use Protected Endpoints

### 1. Generate an API Key
Generate a strong, random API key using one of these methods:

**On Linux/Mac:**
```bash
openssl rand -hex 32
```

**On Windows (PowerShell):**
```powershell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Example output: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 2. Set Environment Variable
Store the API key in your `.env` file or environment variables:

```env
PORTFOLIO_API_KEY=your-generated-api-key-here
```

**Important**: 
- Never commit `.env` file to version control
- Add `.env` to `.gitignore`
- Use different API keys for development and production

### 3. Make Authenticated Requests

#### Delete Contacts
```bash
curl -X DELETE "https://your-api.com/api/contacts" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]}'
```

#### Get Contacts
```bash
curl -X GET "https://your-api.com/api/contacts?page=1&limit=10" \
  -H "X-API-Key: your-api-key-here"
```

#### JavaScript/Fetch Example
```javascript
// Get contacts
const response = await fetch('https://your-api.com/api/contacts?page=1&limit=10', {
  method: 'GET',
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
});

// Delete contacts
const deleteResponse = await fetch('https://your-api.com/api/contacts', {
  method: 'DELETE',
  headers: {
    'X-API-Key': 'your-api-key-here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ids: ['507f1f77bcf86cd799439011', '507f1f77bcf86cd799439012']
  })
});
```

---

## Production Deployment Checklist

- [ ] Generate a strong, random API key (use `openssl rand -hex 32` or equivalent)
- [ ] Set `PORTFOLIO_API_KEY` environment variable on production server
- [ ] Verify CORS origins are correctly restricted to your frontend domain(s)
- [ ] Test protected endpoints with valid API key
- [ ] Test protected endpoints with invalid/missing API key (should return 401)
- [ ] Never expose API key in client-side code or version control
- [ ] Consider rotating API keys periodically
- [ ] Add logging to track API access attempts
- [ ] Monitor for unauthorized access attempts

---

## Additional Security Recommendations

### 1. Rate Limiting
Consider adding rate limiting to prevent brute force attacks:
```bash
pip install slowapi
```

### 2. Enhanced Logging
Add logging to track sensitive operations:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"DELETE request from user attempted")
```

### 3. Multiple API Keys
Consider supporting multiple API keys with different permissions:
- `ADMIN_API_KEY` - For DELETE operations
- `READ_API_KEY` - For GET operations

### 4. JWT Tokens (Advanced)
For more sophisticated authentication, consider using JWT tokens:
```bash
pip install python-jose cryptography
```

### 5. Request Signing
Add request signature verification using HMAC for additional security

---

## Testing

### Test without API Key (should fail)
```bash
curl -X GET "http://localhost:8000/api/contacts"
# Expected: 403 Forbidden - Missing API key header
```

### Test with wrong API Key (should fail)
```bash
curl -X GET "http://localhost:8000/api/contacts" \
  -H "X-API-Key: wrong-key"
# Expected: 401 Unauthorized - Invalid API key
```

### Test with correct API Key (should succeed)
```bash
curl -X GET "http://localhost:8000/api/contacts" \
  -H "X-API-Key: correct-api-key"
# Expected: 200 OK - Returns contacts data
```

---

## Troubleshooting

### "Invalid API key" error
- Verify the API key is set in environment variables
- Check for typos in the API key
- Ensure the header name is exactly `X-API-Key` (case-sensitive in some contexts)

### "API key not configured" error
- The server cannot find the `PORTFOLIO_API_KEY` environment variable
- Set the environment variable and restart the server

### CORS errors in browser
- If browser shows CORS error, ensure your frontend origin is in the `origins` list in `main.py`
- CORS errors are separate from API key authentication

---

## Support
For security issues or questions, please review the SECURITY.md file or contact the development team.
