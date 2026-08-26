package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.CatalogueDtos.ProductCard;
import com.thulya.security.CurrentUser;
import com.thulya.service.WishlistService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/wishlist")
public class WishlistController {

    private final WishlistService wishlist;

    public WishlistController(WishlistService wishlist) {
        this.wishlist = wishlist;
    }

    @GetMapping
    public ApiResponse<List<ProductCard>> list() {
        return ApiResponse.ok(wishlist.list(CurrentUser.id()));
    }

    @PostMapping("/{productId}")
    public ApiResponse<List<ProductCard>> add(@PathVariable String productId) {
        return ApiResponse.ok(wishlist.add(CurrentUser.id(), productId));
    }

    @DeleteMapping("/{productId}")
    public ApiResponse<List<ProductCard>> remove(@PathVariable String productId) {
        return ApiResponse.ok(wishlist.remove(CurrentUser.id(), productId));
    }
}
