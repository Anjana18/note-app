package com.thulya.security;

/** The authenticated principal placed in the SecurityContext. */
public record AuthUser(String id, String role, String name) {
}
