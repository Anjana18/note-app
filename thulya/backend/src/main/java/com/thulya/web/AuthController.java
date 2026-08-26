package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.AuthDtos.*;
import com.thulya.security.CurrentUser;
import com.thulya.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService auth;

    public AuthController(AuthService auth) {
        this.auth = auth;
    }

    /** Dev login (phone -> JWT). Replaced by /firebase in production. */
    @PostMapping("/login")
    public ApiResponse<AuthResponse> login(@Valid @RequestBody LoginRequest req) {
        return ApiResponse.ok(auth.login(req));
    }

    /** Production: exchange a verified Firebase ID token for an app JWT (stub delegates to login logic). */
    @PostMapping("/firebase")
    public ApiResponse<AuthResponse> firebase(@Valid @RequestBody FirebaseAuthRequest req) {
        // TODO: verify req.idToken() with Firebase Admin SDK, then issue tokens for the resolved user.
        throw com.thulya.common.ApiException.badRequest("FIREBASE_NOT_CONFIGURED");
    }

    @PostMapping("/refresh")
    public ApiResponse<AuthResponse> refresh(@Valid @RequestBody RefreshRequest req) {
        return ApiResponse.ok(auth.refresh(req.refreshToken()));
    }

    @GetMapping("/me")
    public ApiResponse<UserView> me() {
        return ApiResponse.ok(auth.me(CurrentUser.id()));
    }
}
