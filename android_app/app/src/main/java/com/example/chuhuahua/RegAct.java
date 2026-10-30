package com.example.chuhuahua;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class RegAct extends AppCompatActivity {

    private static final String PREF_NAME = "ChihuahuaPrefs";
    private static final String KEY_USER_ROLE = "user_role";
    private static final String KEY_PHONE = "user_phone";
    private static final String KEY_USERNAME = "user_username";
    private static final String KEY_PAIRED = "is_paired";

    private EditText etPhone, etUsername, etPassword;
    private Button btnRegister;
    private String userRole = "Patient";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_reg);

        if (getIntent() != null && getIntent().hasExtra("ACCOUNT_TYPE")) {
            userRole = getIntent().getStringExtra("ACCOUNT_TYPE");
        }

        etPhone = findViewById(R.id.etPhone);
        etUsername = findViewById(R.id.etUsername);
        etPassword = findViewById(R.id.etPassword);
        btnRegister = findViewById(R.id.btnRegister);

        SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        boolean isPaired = prefs.getBoolean(KEY_PAIRED, false);

        if (isPaired) {
            String savedRole = prefs.getString(KEY_USER_ROLE, userRole);
            redirectBasedOnRole(savedRole, prefs.getString(KEY_PHONE, ""));
            return;
        }

        if (btnRegister != null) {
            btnRegister.setOnClickListener(v -> handleRegistration());
        }
    }

    private void handleRegistration() {
        String phone = etPhone != null ? etPhone.getText().toString().trim() : "";
        String username = etUsername != null ? etUsername.getText().toString().trim() : "";
        String password = etPassword != null ? etPassword.getText().toString().trim() : "";

        if (phone.isEmpty()) {
            Toast.makeText(this, "Please enter a valid phone number", Toast.LENGTH_SHORT).show();
            return;
        }
        if (username.isEmpty()) {
            Toast.makeText(this, "Please enter a username", Toast.LENGTH_SHORT).show();
            return;
        }
        if (password.isEmpty()) {
            Toast.makeText(this, "Please enter a password", Toast.LENGTH_SHORT).show();
            return;
        }

        // Save account details securely in SharedPreferences
        SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        prefs.edit()
                .putBoolean(KEY_PAIRED, true)
                .putString(KEY_USER_ROLE, userRole)
                .putString(KEY_PHONE, phone)
                .putString(KEY_USERNAME, username)
                .apply();

        // Also update general user login state if used by MainActivity
        SharedPreferences userPrefs = getSharedPreferences("UserPrefs", MODE_PRIVATE);
        userPrefs.edit()
                .putBoolean("IS_LOGGED_IN", true)
                .putString("ACCOUNT_TYPE", userRole)
                .apply();

        Toast.makeText(this, "Account created successfully!", Toast.LENGTH_SHORT).show();
        redirectBasedOnRole(userRole, phone);
    }

    private void redirectBasedOnRole(String role, String phone) {
        Intent intent;
        if (role != null && role.equalsIgnoreCase("Caretaker")) {
            intent = new Intent(RegAct.this, CaretakerActivity.class);
        } else {
            intent = new Intent(RegAct.this, PatientActivity.class);
        }
        intent.putExtra("USER_PHONE", phone);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}