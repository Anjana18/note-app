package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.TailoringDtos.*;
import com.thulya.service.TailoringPricingService;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/tailoring")
public class TailoringController {

    private final TailoringPricingService tailoring;

    public TailoringController(TailoringPricingService tailoring) {
        this.tailoring = tailoring;
    }

    @GetMapping("/services")
    public ApiResponse<List<GroupView>> services() {
        return ApiResponse.ok(tailoring.groups());
    }

    @PutMapping("/services/{itemCode}")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<ItemView> updatePrice(@PathVariable String itemCode,
                                             @Valid @RequestBody UpdatePriceRequest req) {
        return ApiResponse.ok(tailoring.updatePrice(itemCode, req.price()));
    }
}
