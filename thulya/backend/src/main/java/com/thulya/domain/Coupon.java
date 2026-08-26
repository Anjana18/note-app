package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Document("coupons")
public class Coupon {

    @Id
    private String id;

    @Indexed(unique = true)
    private String code;

    private String type = "percent"; // percent | flat
    private int value;               // percent value, or flat rupees
    private long maxDiscount;        // paise, 0 = no cap
    private long minOrder;           // paise
    private String festival;

    private int usageLimit;
    private int usedCount;
    private int perUserLimit = 1;

    private Instant startsAt;
    private Instant endsAt;
    private boolean active = true;
}
