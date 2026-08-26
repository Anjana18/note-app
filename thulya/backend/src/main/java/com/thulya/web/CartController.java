package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.CartDtos.*;
import com.thulya.security.CurrentUser;
import com.thulya.service.CartService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/cart")
public class CartController {

    private final CartService cart;

    public CartController(CartService cart) {
        this.cart = cart;
    }

    @GetMapping
    public ApiResponse<CartView> view() {
        return ApiResponse.ok(cart.view(CurrentUser.id()));
    }

    @PostMapping("/items")
    public ApiResponse<CartView> add(@Valid @RequestBody AddItemRequest req) {
        return ApiResponse.ok(cart.addItem(CurrentUser.id(), req));
    }

    @PatchMapping("/items/{itemId}")
    public ApiResponse<CartView> update(@PathVariable String itemId, @Valid @RequestBody UpdateItemRequest req) {
        return ApiResponse.ok(cart.updateItem(CurrentUser.id(), itemId, req.qty()));
    }

    @DeleteMapping("/items/{itemId}")
    public ApiResponse<CartView> remove(@PathVariable String itemId) {
        return ApiResponse.ok(cart.removeItem(CurrentUser.id(), itemId));
    }

    @PostMapping("/apply-coupon")
    public ApiResponse<CartView> applyCoupon(@Valid @RequestBody ApplyCouponRequest req) {
        return ApiResponse.ok(cart.applyCoupon(CurrentUser.id(), req.code()));
    }
}
