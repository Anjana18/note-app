package com.thulya.dto;

import jakarta.validation.constraints.NotBlank;

import java.time.Instant;
import java.util.Map;

public final class MeasurementDtos {

    private MeasurementDtos() {}

    public record CreateMeasurementRequest(@NotBlank String dressType,
                                           Map<String, Object> values, String takenBy) {}

    public record MeasurementView(String id, String dressType, Map<String, Object> values,
                                  String takenBy, Instant takenAt) {}
}
