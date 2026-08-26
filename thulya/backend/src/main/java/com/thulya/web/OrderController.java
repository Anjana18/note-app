package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.OrderDtos.*;
import com.thulya.security.CurrentUser;
import com.thulya.service.OrderService;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderService orders;

    public OrderController(OrderService orders) {
        this.orders = orders;
    }

    @PostMapping
    public ApiResponse<OrderView> create(@RequestBody(required = false) CreateOrderRequest req) {
        CreateOrderRequest r = req != null ? req : new CreateOrderRequest(null, "full");
        return ApiResponse.ok(orders.createFromCart(CurrentUser.id(), r));
    }

    @GetMapping
    public ApiResponse<List<OrderView>> myOrders() {
        return ApiResponse.ok(orders.myOrders(CurrentUser.id()));
    }

    @GetMapping("/{orderNo}")
    public ApiResponse<OrderView> get(@PathVariable String orderNo) {
        return ApiResponse.ok(orders.get(orderNo, CurrentUser.id()));
    }

    @GetMapping("/{orderNo}/track")
    public ApiResponse<TrackView> track(@PathVariable String orderNo) {
        return ApiResponse.ok(orders.track(orderNo));
    }

    @PatchMapping("/{orderNo}/stage")
    @PreAuthorize("hasAnyRole('ADMIN','TAILOR')")
    public ApiResponse<OrderView> updateStage(@PathVariable String orderNo,
                                              @Valid @RequestBody StageUpdateRequest req) {
        return ApiResponse.ok(orders.updateStage(orderNo, req, CurrentUser.id()));
    }

    @PatchMapping("/{orderNo}/assign")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<OrderView> assign(@PathVariable String orderNo,
                                         @Valid @RequestBody AssignTailorRequest req) {
        return ApiResponse.ok(orders.assignTailor(orderNo, req.tailorId()));
    }
}
