# Security Headers Configuration

## Overview

The FastAPI application implements comprehensive security headers to protect against common web vulnerabilities. The security headers middleware automatically adds essential security headers to all responses, with special handling for API documentation endpoints.

## Content Security Policy (CSP)

### Dual CSP Configuration

The application uses different CSP policies for different types of endpoints:

#### 1. API Endpoints (Strict CSP)
For all API endpoints (`/api/v1/*`), a strict CSP is applied:

```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self';
connect-src 'self';
frame-ancestors 'none';
```

#### 2. Documentation Endpoints (Relaxed CSP)
For documentation endpoints (`/docs`, `/redoc`, `/openapi.json`), a relaxed CSP allows external resources:

```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: https:;
connect-src 'self';
frame-ancestors 'none';
```

### CSP Configuration Options

Control CSP behavior through environment variables:

```bash
# Enable/disable CSP (default: true)
CSP_ENABLED=true

# Use report-only mode for testing (default: false)
CSP_REPORT_ONLY=false
```

### Why Different CSP Policies?

1. **Security**: API endpoints need strict CSP to prevent XSS and injection attacks
2. **Functionality**: Swagger UI requires external resources (CDN scripts, fonts, styles)
3. **Balance**: Maintains security while preserving documentation functionality

## Complete Security Headers

### Standard Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking attacks |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS protection (legacy browsers) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information |

### HTTPS Security (Production Only)

When `ENVIRONMENT=production` and `COOKIE_SECURE=true`:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS connections |

### Cache Control (Sensitive Endpoints)

For authentication and user endpoints:

| Header | Value | Purpose |
|--------|-------|---------|
| `Cache-Control` | `no-store, no-cache, must-revalidate, private` | Prevent caching of sensitive data |
| `Pragma` | `no-cache` | Legacy cache control |
| `Expires` | `0` | Immediate expiration |

### Permissions Policy

Restricts access to browser features:

```
geolocation=(),
microphone=(),
camera=(),
payment=(),
usb=(),
magnetometer=(),
gyroscope=(),
speaker=()
```

## Troubleshooting CSP Issues

### Common CSP Violations

#### 1. External Scripts Blocked
**Error**: `Refused to load script because it violates CSP directive`

**Solution**: 
- For API endpoints: This is expected and secure
- For docs: Check if the domain is in the allowed list

#### 2. Inline Styles Blocked
**Error**: `Refused to apply inline style because it violates CSP directive`

**Solution**: Use external stylesheets or add `'unsafe-inline'` to style-src (already included)

#### 3. External Fonts Blocked
**Error**: `Refused to load font because it violates CSP directive`

**Solution**: Add the font domain to font-src directive

### CSP Testing Mode

Use report-only mode to test CSP without blocking resources:

```bash
# Enable report-only mode
CSP_REPORT_ONLY=true
```

In report-only mode, violations are logged but resources are not blocked.

### Custom CSP Configuration

To customize CSP for your specific needs, modify the middleware:

```python
# app/middleware/security_headers.py

# For stricter security (production)
csp_policy = (
    "default-src 'none'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

# For development (more permissive)
csp_policy = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)
```

## Security Headers Best Practices

### 1. Production Deployment

```bash
# Environment variables for production
ENVIRONMENT=production
COOKIE_SECURE=true
CSP_ENABLED=true
CSP_REPORT_ONLY=false
```

### 2. Development Setup

```bash
# Environment variables for development
ENVIRONMENT=development
COOKIE_SECURE=false
CSP_ENABLED=true
CSP_REPORT_ONLY=true  # Test CSP without blocking
```

### 3. Staging Environment

```bash
# Environment variables for staging
ENVIRONMENT=staging
COOKIE_SECURE=true
CSP_ENABLED=true
CSP_REPORT_ONLY=false
```

## Monitoring and Compliance

### CSP Violation Reporting

To implement CSP violation reporting, add a report-uri directive:

```python
csp_policy += "report-uri /api/v1/csp-report;"
```

### Security Headers Validation

Check security headers using online tools:
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)

### Expected Security Grades

With all headers properly configured:
- **Security Headers**: A+ grade
- **Mozilla Observatory**: A+ grade
- **OWASP Compliance**: Meets security standards

## Troubleshooting Guide

### Issue: Swagger UI Not Loading

**Symptoms**: Blank documentation page, console errors about blocked resources

**Solution**: 
1. Check if CSP is enabled: `CSP_ENABLED=true`
2. Verify documentation endpoints are detected correctly
3. Ensure external domains are allowed in docs CSP

### Issue: API Responses Blocked

**Symptoms**: API calls fail with CSP violations

**Solution**:
1. Check connect-src directive includes your API domain
2. Verify CORS configuration allows your frontend domain
3. Ensure API endpoints use strict CSP, not docs CSP

### Issue: Custom Fonts Not Loading

**Symptoms**: Fonts fall back to system defaults

**Solution**:
1. Add font domain to font-src directive
2. Ensure HTTPS is used for external fonts in production
3. Consider self-hosting fonts for better security

## Security Considerations

### 1. CSP Bypass Prevention
- Never use `'unsafe-eval'` in production API endpoints
- Limit `'unsafe-inline'` usage to necessary cases only
- Regularly audit and tighten CSP directives

### 2. Header Injection Prevention
- All header values are properly escaped
- No user input is directly included in headers
- Headers are set server-side only

### 3. Performance Impact
- Headers add minimal overhead (~1KB per response)
- CSP parsing is done by browser, not server
- Caching headers improve performance for static resources

The security headers implementation provides comprehensive protection while maintaining functionality for API documentation and development workflows.
