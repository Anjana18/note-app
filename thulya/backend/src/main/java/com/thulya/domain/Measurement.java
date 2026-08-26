package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@Data
@Document("measurements")
public class Measurement {

    @Id
    private String id;

    @Indexed
    private String userId;

    private String dressType;  // blouse, salwar, anarkali, lehenga, gown, kids
    private Map<String, Object> values = new LinkedHashMap<>(); // bust, waist, ... + unit
    private String takenBy;    // doorstep | boutique | video | self
    private boolean active = true;
    private Instant takenAt = Instant.now();
}
