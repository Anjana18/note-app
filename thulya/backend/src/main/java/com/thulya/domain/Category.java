package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Document("categories")
public class Category {

    @Id
    private String id;

    private String name;

    @Indexed(unique = true)
    private String slug;

    /** null for a top-level category, else the parent category id. */
    private String parentId;

    private String icon;
    private int order;
    private boolean active = true;
}
