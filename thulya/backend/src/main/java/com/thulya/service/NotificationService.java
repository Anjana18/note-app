package com.thulya.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Outbound notifications (WhatsApp / push / SMS / email).
 * This slice logs the intent; production wires the WhatsApp Business API and FCM here.
 */
@Service
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);

    public void send(String userId, String channel, String template, String message) {
        log.info("[notify] user={} channel={} template={} :: {}", userId, channel, template, message);
        // TODO: integrate WhatsApp Business API / FCM / SMS / email providers.
    }
}
