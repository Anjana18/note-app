package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("carts")
public class Cart {

    @Id
    private String id;

    @Indexed(unique = true)
    private String userId;

    private List<CartItem> items = new ArrayList<>();
    private String couponCode;
    private Instant updatedAt = Instant.now();

    @Data
    public static class CartItem {
        private String itemId;     // client-side line id
        private String productId;
        private String size;
        private int qty;
    }
}
