package com.thulya.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

import java.util.List;

/** Cart request/response payloads. Money in rupees. */
public final class CartDtos {

    private CartDtos() {}

    public record AddItemRequest(@NotBlank String productId, String size, @Min(1) int qty) {}

    public record UpdateItemRequest(@Min(0) int qty) {}

    public record ApplyCouponRequest(@NotBlank String code) {}

    public record CartLine(String itemId, String productId, String name, String image,
                           String size, int qty, long unitPrice, long lineTotal) {}

    public record CartView(List<CartLine> items, long subtotal, long discount,
                           long gst, long shipping, long total, String couponCode) {}
}
