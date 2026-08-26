package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.OrderDtos.OrderView;
import com.thulya.security.CurrentUser;
import com.thulya.service.OrderService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/tailor")
@PreAuthorize("hasAnyRole('TAILOR','ADMIN')")
public class TailorController {

    private final OrderService orders;

    public TailorController(OrderService orders) {
        this.orders = orders;
    }

    /** Jobs assigned to the signed-in tailor. */
    @GetMapping("/jobs")
    public ApiResponse<List<OrderView>> jobs() {
        return ApiResponse.ok(orders.tailorQueue(CurrentUser.id()));
    }
}
