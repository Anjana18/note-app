package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("appointments")
public class Appointment {

    @Id
    private String id;

    @Indexed
    private String userId;

    private AppointmentMode mode = AppointmentMode.DOORSTEP;
    private String dressType;
    private String service;

    private Slot slot = new Slot();
    private String addressId;
    private String notes;

    private AppointmentStatus status = AppointmentStatus.CONFIRMED;
    private List<String> remindersSent = new ArrayList<>();
    private Instant createdAt = Instant.now();

    @Data
    public static class Slot {
        private String date;   // ISO date yyyy-MM-dd
        private String start;  // HH:mm
        private String end;    // HH:mm
    }
}
