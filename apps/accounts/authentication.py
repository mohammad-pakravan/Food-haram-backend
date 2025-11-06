from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.encoding import smart_bytes


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that reads token from HTTP Only Cookie.
    Falls back to header-based authentication if cookie is not found.
    """
    
    def authenticate(self, request):
        # First try to get token from cookie
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            # If no cookie, try to get from header (fallback)
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
        else:
            # Token found in cookie, convert to bytes
            raw_token = smart_bytes(raw_token)
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError) as e:
            return None
        except Exception:
            return None

        return self.get_user(validated_token), validated_token

