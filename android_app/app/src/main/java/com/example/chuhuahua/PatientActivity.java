package com.example.chuhuahua;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class PatientActivity extends AppCompatActivity {

    private static final String PREF_NAME = "PatientPrefs";
    private static final String KEY_ROBOT_IP = "robot_ip";

    private EditText etRobotIp;
    private Button btnConnectPatient;
    private String userPhone;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_patient);

        userPhone = getIntent().getStringExtra("USER_PHONE");

        SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        String savedIp = prefs.getString(KEY_ROBOT_IP, "");
        if (!savedIp.isEmpty()) {
            Intent intent = new Intent(this, Patient_Main.class);
            intent.putExtra("ROBOT_IP", savedIp);
            intent.putExtra("USER_PHONE", userPhone);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            finish();
            return;
        }

        etRobotIp = findViewById(R.id.etRobotInfo);
        btnConnectPatient = findViewById(R.id.btnSavePatientSetup);

        if (btnConnectPatient != null) {
            btnConnectPatient.setOnClickListener(v -> {
                String ip = etRobotIp != null ? etRobotIp.getText().toString().trim() : "";

                if (ip.isEmpty()) {
                    Toast.makeText(PatientActivity.this, "Please enter a valid Robot IP", Toast.LENGTH_SHORT).show();
                    return;
                }

                // Save the robot IP persistently using SharedPreferences
                SharedPreferences sharedPreferences = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                sharedPreferences.edit().putString(KEY_ROBOT_IP, ip).apply();

                // Navigate directly to the Patient Main activity
                Intent intent = new Intent(PatientActivity.this, Patient_Main.class);
                intent.putExtra("ROBOT_IP", ip);
                intent.putExtra("USER_PHONE", userPhone);
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                startActivity(intent);
                finish();
            });
        }
    }
}