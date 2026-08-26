package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.AdminDtos.AnalyticsView;
import com.thulya.service.AdminAnalyticsService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    private final AdminAnalyticsService analytics;

    public AdminController(AdminAnalyticsService analytics) {
        this.analytics = analytics;
    }

    @GetMapping("/analytics")
    public ApiResponse<AnalyticsView> analytics() {
        return ApiResponse.ok(analytics.analytics());
    }
}
