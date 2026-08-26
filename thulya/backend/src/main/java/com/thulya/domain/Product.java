package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("products")
public class Product {

    @Id
    private String id;

    @Indexed(unique = true)
    private String sku;

    private String name;

    @Indexed(unique = true)
    private String slug;

    private String category;      // leaf category name, e.g. "Sarees"
    private String subCategory;   // e.g. "Kanjivaram"

    private String description;
    private List<String> images = new ArrayList<>();
    private String video;

    private String fabric;
    private String washCare;
    private List<Size> sizes = new ArrayList<>();

    /** Money in paise. */
    private long priceMrp;
    private long priceOffer;
    private int gstPct = 5;

    private int deliveryMinDays;
    private int deliveryMaxDays;
    private int stock;

    private List<String> tags = new ArrayList<>();

    private double ratingAvg;
    private int ratingCount;

    private List<String> relatedProductIds = new ArrayList<>();

    private boolean active = true;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    @Data
    public static class Size {
        private String label;
        private int stock;

        public Size(String label, int stock) {
            this.label = label;
            this.stock = stock;
        }
    }
}
