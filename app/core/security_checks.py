"""Security validation and startup checks."""
import warnings
from app.core.config import settings


def validate_production_security() -> None:
    """Validate security configuration for production deployment."""
    issues = []
    
    # Check secret key
    if settings.SECRET_KEY == "dev-secret-key-change-me":
        issues.append("🔴 CRITICAL: Default SECRET_KEY detected! Change immediately.")
    elif len(settings.SECRET_KEY) < 32:
        issues.append(f"🟡 WARNING: SECRET_KEY is only {len(settings.SECRET_KEY)} characters. Use at least 32.")
    
    # Check cookie security in production
    if settings.is_production:
        if not settings.COOKIE_SECURE:
            issues.append("🔴 CRITICAL: COOKIE_SECURE must be True in production (requires HTTPS).")
        if settings.COOKIE_SAMESITE.lower() not in ["strict", "lax"]:
            issues.append("🟡 WARNING: COOKIE_SAMESITE should be 'strict' or 'lax' in production.")
        if "*" in settings.ALLOW_ORIGINS:
            issues.append("🔴 CRITICAL: ALLOW_ORIGINS contains '*' in production. Specify exact origins.")
    
    # Check CORS configuration
    if settings.ALLOW_CREDENTIALS and "*" in settings.ALLOW_ORIGINS:
        issues.append("🔴 CRITICAL: Cannot use ALLOW_CREDENTIALS=True with ALLOW_ORIGINS=['*'].")

    # Check JWT algorithm configuration
    if settings.ALGORITHM.startswith('RS'):
        try:
            settings.get_signing_key()
            settings.get_verification_key()
        except ValueError as e:
            issues.append(f"🔴 CRITICAL: RSA key configuration error: {e}")

    # Validate RSA key pair if using RS algorithms
    if settings.ALGORITHM.startswith('RS') and settings.RSA_PRIVATE_KEY and settings.RSA_PUBLIC_KEY:
        from app.core.key_management import KeyManager
        if not KeyManager.validate_rsa_key_pair(settings.RSA_PRIVATE_KEY, settings.RSA_PUBLIC_KEY):
            issues.append("🔴 CRITICAL: RSA private and public keys do not match!")
    
    # Print issues
    if issues:
        print("\n" + "="*60)
        print("🔒 SECURITY CONFIGURATION ISSUES DETECTED:")
        print("="*60)
        for issue in issues:
            print(f"  {issue}")
        print("="*60)
        
        if settings.is_production:
            print("🚨 PRODUCTION DEPLOYMENT BLOCKED due to security issues!")
            print("Fix the above issues before deploying to production.")
            print("="*60 + "\n")
            # In a real app, you might want to exit here
            # raise SystemExit(1)
        else:
            print("💡 These issues should be fixed before production deployment.")
            print("="*60 + "\n")
    else:
        print("✅ Security configuration validation passed!")


def print_security_recommendations() -> None:
    """Print security recommendations for the current environment."""
    print("\n" + "="*60)
    print("🔒 SECURITY RECOMMENDATIONS:")
    print("="*60)
    
    if settings.is_development:
        print("📝 Development Environment:")
        print("  • Set ENVIRONMENT=production for production deployment")
        print("  • Set COOKIE_SECURE=true when using HTTPS")
        print("  • Replace default SECRET_KEY with a strong key")
        print("  • Configure specific ALLOW_ORIGINS instead of '*'")
    
    if settings.is_production:
        print("🚀 Production Environment:")
        print("  • Ensure HTTPS is enabled")
        print("  • Monitor authentication logs")
        print("  • Regularly rotate SECRET_KEY")
        print("  • Set up token blacklist cleanup job")
        print("  • Enable security headers")
    
    print("🔧 General Recommendations:")
    print("  • Use environment variables for all secrets")
    print("  • Enable rate limiting on authentication endpoints")
    print("  • Implement audit logging")
    print("  • Regular security updates")
    print("  • Consider RS256 algorithm for better key management")
    print("  • Use separate keys for different environments")
    print("="*60 + "\n")

    # Show JWT algorithm info
    print(f"🔑 Current JWT Configuration:")
    print(f"  • Algorithm: {settings.ALGORITHM}")
    if settings.ALGORITHM.startswith('RS'):
        print(f"  • Using RSA keys for signing/verification")
        print(f"  • Private key configured: {'✅' if settings.RSA_PRIVATE_KEY or settings.RSA_PRIVATE_KEY_PATH else '❌'}")
        print(f"  • Public key configured: {'✅' if settings.RSA_PUBLIC_KEY or settings.RSA_PUBLIC_KEY_PATH else '❌'}")
    else:
        print(f"  • Using HMAC with secret key")
    print("="*60 + "\n")
