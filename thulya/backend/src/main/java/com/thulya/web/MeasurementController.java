package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.MeasurementDtos.*;
import com.thulya.security.CurrentUser;
import com.thulya.service.MeasurementService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/measurements")
public class MeasurementController {

    private final MeasurementService measurements;

    public MeasurementController(MeasurementService measurements) {
        this.measurements = measurements;
    }

    @GetMapping
    public ApiResponse<List<MeasurementView>> list() {
        return ApiResponse.ok(measurements.list(CurrentUser.id()));
    }

    @PostMapping
    public ApiResponse<MeasurementView> create(@Valid @RequestBody CreateMeasurementRequest req) {
        return ApiResponse.ok(measurements.create(CurrentUser.id(), req));
    }
}
