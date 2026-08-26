package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.AppointmentDtos.*;
import com.thulya.security.CurrentUser;
import com.thulya.service.AppointmentService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/appointments")
public class AppointmentController {

    private final AppointmentService appointments;

    public AppointmentController(AppointmentService appointments) {
        this.appointments = appointments;
    }

    /** Public: available slots for a date. */
    @GetMapping("/slots")
    public ApiResponse<List<SlotView>> slots(@RequestParam String date) {
        return ApiResponse.ok(appointments.slots(date));
    }

    @PostMapping
    public ApiResponse<AppointmentView> create(@Valid @RequestBody CreateAppointmentRequest req) {
        return ApiResponse.ok(appointments.create(CurrentUser.id(), req));
    }

    @GetMapping
    public ApiResponse<List<AppointmentView>> mine() {
        return ApiResponse.ok(appointments.myAppointments(CurrentUser.id()));
    }
}
