package com.thulya.dto;

import jakarta.validation.constraints.NotBlank;

/** Authentication request/response payloads. */
public final class AuthDtos {

    private AuthDtos() {}

    /**
     * Dev login: issues a JWT directly from a phone number so the API is runnable
     * without Firebase. In production this endpoint is replaced by {@link FirebaseAuthRequest}.
     */
    public record LoginRequest(@NotBlank String phone, String name, String role) {}

    /** Production path: exchange a verified Firebase ID token for an app JWT. */
    public record FirebaseAuthRequest(@NotBlank String idToken) {}

    public record RefreshRequest(@NotBlank String refreshToken) {}

    public record UserView(String id, String name, String phone, String email,
                           String role, String loyaltyTier, int loyaltyPoints) {}

    public record AuthResponse(String accessToken, String refreshToken, UserView user) {}
}
