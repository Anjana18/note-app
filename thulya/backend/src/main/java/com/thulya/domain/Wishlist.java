package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("wishlists")
public class Wishlist {

    @Id
    private String id;

    @Indexed(unique = true)
    private String userId;

    private List<String> productIds = new ArrayList<>();
    private Instant updatedAt = Instant.now();
}
