package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.domain.Role;
import com.thulya.domain.User;
import com.thulya.dto.AuthDtos.AuthResponse;
import com.thulya.dto.AuthDtos.LoginRequest;
import com.thulya.dto.AuthDtos.UserView;
import com.thulya.repository.UserRepository;
import com.thulya.security.JwtService;
import io.jsonwebtoken.Claims;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserRepository users;
    private final JwtService jwt;

    public AuthService(UserRepository users, JwtService jwt) {
        this.users = users;
        this.jwt = jwt;
    }

    /**
     * Dev/demo login. Looks up (or creates) a user by phone and issues tokens.
     * Replace with Firebase ID-token verification in production; the token
     * issuance below is identical once the verified phone/uid is known.
     */
    public AuthResponse login(LoginRequest req) {
        User user = users.findByPhone(req.phone()).orElseGet(() -> {
            User u = new User();
            u.setPhone(req.phone());
            u.setName(req.name() != null ? req.name() : "Guest");
            u.setRole(parseRole(req.role()));
            return users.save(u);
        });
        return tokensFor(user);
    }

    public AuthResponse refresh(String refreshToken) {
        Claims claims;
        try {
            claims = jwt.parse(refreshToken);
        } catch (Exception e) {
            throw ApiException.badRequest("INVALID_REFRESH_TOKEN");
        }
        if (!"refresh".equals(claims.get("typ", String.class))) {
            throw ApiException.badRequest("INVALID_REFRESH_TOKEN");
        }
        User user = users.findById(claims.getSubject())
                .orElseThrow(() -> ApiException.notFound("USER_NOT_FOUND"));
        return tokensFor(user);
    }

    public UserView me(String userId) {
        return view(users.findById(userId).orElseThrow(() -> ApiException.notFound("USER_NOT_FOUND")));
    }

    private AuthResponse tokensFor(User user) {
        String access = jwt.issueAccess(user.getId(), user.getRole().name(), user.getName());
        String refresh = jwt.issueRefresh(user.getId());
        return new AuthResponse(access, refresh, view(user));
    }

    private UserView view(User u) {
        return new UserView(u.getId(), u.getName(), u.getPhone(), u.getEmail(),
                u.getRole().name(), u.getLoyaltyTier(), u.getLoyaltyPoints());
    }

    private Role parseRole(String role) {
        if (role == null) return Role.CUSTOMER;
        try {
            return Role.valueOf(role.toUpperCase());
        } catch (IllegalArgumentException e) {
            return Role.CUSTOMER;
        }
    }
}
