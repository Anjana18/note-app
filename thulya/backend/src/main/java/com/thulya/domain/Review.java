package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("reviews")
public class Review {

    @Id
    private String id;

    @Indexed
    private String productId;
    private String userId;
    private String userName;

    private int rating;      // 1..5
    private String text;
    private List<String> images = new ArrayList<>();

    private boolean verifiedPurchase;
    private String orderId;
    private Instant createdAt = Instant.now();
}
