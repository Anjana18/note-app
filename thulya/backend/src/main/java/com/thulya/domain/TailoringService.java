package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/** A group of tailoring price items (Admin-editable). */
@Data
@Document("tailoringServices")
public class TailoringService {

    @Id
    private String id;

    private String group;   // e.g. "Blouse Stitching"
    private String icon;
    private List<Item> items = new ArrayList<>();
    private boolean active = true;
    private Instant updatedAt = Instant.now();

    @Data
    public static class Item {
        private String code;     // unique within catalogue, e.g. "blouse_dart"
        private String name;
        private long price;      // paise
        private boolean fromPrice; // true => "starting at"

        public Item(String code, String name, long price, boolean fromPrice) {
            this.code = code;
            this.name = name;
            this.price = price;
            this.fromPrice = fromPrice;
        }
    }
}
