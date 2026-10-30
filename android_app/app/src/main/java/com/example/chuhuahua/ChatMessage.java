package com.example.chuhuahua;

public class ChatMessage {
    private String message;
    private boolean isImage;

    public ChatMessage(String message, boolean isImage) {
        this.message = message;
        this.isImage = isImage;
    }

    public String getMessage() {
        return message;
    }

    public boolean isImage() {
        return isImage;
    }
}