package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Singleton config controlling appointment availability. */
@Data
@Document("calendarConfig")
public class CalendarConfig {

    @Id
    private String id;

    /** Day-of-week (mon..sun) -> ["10:00","19:00"] or absent = closed. */
    private Map<String, List<String>> workingHours = new LinkedHashMap<>();

    private int slotMinutes = 60;
    private int maxPerSlot = 3;

    private List<String> holidays = new ArrayList<>();      // yyyy-MM-dd
    private List<String> blockedDates = new ArrayList<>();  // yyyy-MM-dd
}
