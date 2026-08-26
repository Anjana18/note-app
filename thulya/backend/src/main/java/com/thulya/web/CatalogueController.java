package com.thulya.web;

import com.thulya.common.ApiResponse;
import com.thulya.dto.CatalogueDtos.*;
import com.thulya.service.CatalogueService;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
public class CatalogueController {

    private final CatalogueService catalogue;

    public CatalogueController(CatalogueService catalogue) {
        this.catalogue = catalogue;
    }

    @GetMapping("/categories")
    public ApiResponse<List<CategoryView>> categories() {
        return ApiResponse.ok(catalogue.categories());
    }

    @GetMapping("/products")
    public ApiResponse<List<ProductCard>> products(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String sort,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Page<ProductCard> result = catalogue.listProducts(category, q, sort, page, size);
        return ApiResponse.ok(result.getContent(),
                new ApiResponse.PageMeta(result.getNumber(), result.getSize(), result.getTotalElements()));
    }

    @GetMapping("/products/{slugOrId}")
    public ApiResponse<ProductDetail> product(@PathVariable String slugOrId) {
        return ApiResponse.ok(catalogue.productDetail(slugOrId));
    }

    @GetMapping("/products/{id}/related")
    public ApiResponse<List<ProductCard>> related(@PathVariable String id) {
        return ApiResponse.ok(catalogue.related(id));
    }

    @GetMapping("/products/{id}/reviews")
    public ApiResponse<List<ReviewView>> reviews(@PathVariable String id) {
        return ApiResponse.ok(catalogue.reviews(id));
    }
}
