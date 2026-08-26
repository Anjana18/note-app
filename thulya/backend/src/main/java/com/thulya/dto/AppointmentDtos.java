package com.thulya.dto;

import jakarta.validation.constraints.NotBlank;

import java.time.Instant;

/** Appointment + measurement payloads. */
public final class AppointmentDtos {

    private AppointmentDtos() {}

    public record CreateAppointmentRequest(
            @NotBlank String mode, String dressType, String service,
            @NotBlank String date, @NotBlank String start, String end,
            String addressId, String notes) {}

    public record AppointmentView(String id, String mode, String dressType, String service,
                                  String date, String start, String end,
                                  String status, Instant createdAt) {}

    public record SlotView(String date, String start, String end, boolean available, int remaining) {}
}
