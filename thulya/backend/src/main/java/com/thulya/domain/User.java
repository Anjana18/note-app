package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("users")
public class User {

    @Id
    private String id;

    private Role role = Role.CUSTOMER;
    private String name;

    @Indexed(unique = true)
    private String phone;

    @Indexed(unique = true, sparse = true)
    private String email;

    /** Firebase UID once Firebase Auth is wired in; null for dev logins. */
    @Indexed(sparse = true)
    private String firebaseUid;

    private String avatarUrl;
    private List<Address> addresses = new ArrayList<>();

    private String loyaltyTier = "silver"; // silver | gold | platinum
    private int loyaltyPoints = 0;

    /** Admin-set per-customer pricing. */
    private boolean specialPricing = false;
    private int specialDiscountPct = 0;

    /** Populated only for TAILOR role. */
    private TailorProfile tailorProfile;

    private List<String> fcmTokens = new ArrayList<>();

    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    @Data
    public static class Address {
        private String id;
        private String label;
        private String line1;
        private String city;
        private String state;
        private String pincode;
        private boolean isDefault;
        private Double lat;
        private Double lng;
    }

    @Data
    public static class TailorProfile {
        private double rating = 5.0;
        private int jobsCompleted = 0;
        private List<String> skills = new ArrayList<>();
    }
}
