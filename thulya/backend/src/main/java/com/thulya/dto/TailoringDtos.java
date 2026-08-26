package com.thulya.dto;

import jakarta.validation.constraints.Min;

import java.util.List;

/** Tailoring service payloads. Money in rupees. */
public final class TailoringDtos {

    private TailoringDtos() {}

    public record ItemView(String code, String name, long price, boolean fromPrice) {}

    public record GroupView(String id, String group, String icon, List<ItemView> items) {}

    /** Admin price update (rupees). */
    public record UpdatePriceRequest(@Min(0) long price) {}
}
