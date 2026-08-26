package com.thulya.common;

/**
 * Uniform response envelope: { success, data, message, meta }.
 */
public record ApiResponse<T>(boolean success, T data, String message, PageMeta meta) {

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(true, data, null, null);
    }

    public static <T> ApiResponse<T> ok(T data, PageMeta meta) {
        return new ApiResponse<>(true, data, null, meta);
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, null, message, null);
    }

    /** Pagination metadata. */
    public record PageMeta(int page, int size, long total) {}
}
