package com.thulya.security;

import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class JwtServiceTest {

    private final JwtService jwt =
            new JwtService("test-secret-key-that-is-at-least-32-bytes-long-000", 120, 30);

    @Test
    void issuesAndParsesAccessTokenWithClaims() {
        String token = jwt.issueAccess("user-1", "ADMIN", "Divya");
        Claims claims = jwt.parse(token);
        assertEquals("user-1", claims.getSubject());
        assertEquals("ADMIN", claims.get("role", String.class));
        assertEquals("Divya", claims.get("name", String.class));
        assertEquals("access", claims.get("typ", String.class));
    }

    @Test
    void refreshTokenIsTypedRefresh() {
        Claims claims = jwt.parse(jwt.issueRefresh("user-2"));
        assertEquals("user-2", claims.getSubject());
        assertEquals("refresh", claims.get("typ", String.class));
    }

    @Test
    void tamperedTokenFailsVerification() {
        String token = jwt.issueAccess("user-3", "CUSTOMER", "X");
        String tampered = token.substring(0, token.length() - 2) + "xx";
        assertThrows(Exception.class, () -> jwt.parse(tampered));
    }
}
