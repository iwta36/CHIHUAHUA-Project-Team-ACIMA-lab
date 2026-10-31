package com.example.chuhuahua;

import android.app.TimePickerDialog;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.IOException;
import java.util.Calendar;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class Patient_Main extends AppCompatActivity {

    private static final String PREF_NAME = "PatientPrefs";
    private static final String KEY_ROBOT_IP = "robot_ip";

    private TextView tvSelectedTime;
    private Button btnSetTime, btnDismissAlarm;
    private SharedPreferences prefs;
    private OkHttpClient client;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_patient_main);

        tvSelectedTime = findViewById(R.id.tvSelectedTime);
        btnSetTime = findViewById(R.id.btnSetTime);
        btnDismissAlarm = findViewById(R.id.btnDismissAlarm);

        // Χρησιμοποιούμε το ίδιο ακριβώς PREF_NAME ("PatientPrefs") για να βρίσκει την αποθηκευμένη IP
        prefs = getSharedPreferences(PREF_NAME, MODE_PRIVATE);
        client = new OkHttpClient();

        String savedTime = prefs.getString("PILL_TIME", "");
        if (!savedTime.isEmpty()) {
            tvSelectedTime.setText("Scheduled Pill Time: " + savedTime);
        }

        btnSetTime.setOnClickListener(v -> showTimePicker());
        btnDismissAlarm.setOnClickListener(v -> sendClearCommandToRobot());
    }

    private void showTimePicker() {
        Calendar calendar = Calendar.getInstance();
        int hour = calendar.get(Calendar.HOUR_OF_DAY);
        int minute = calendar.get(Calendar.MINUTE);

        TimePickerDialog timePickerDialog = new TimePickerDialog(this, (view, selectedHour, selectedMinute) -> {
            String formattedTime = String.format("%02d:%02d", selectedHour, selectedMinute);
            prefs.edit().putString("PILL_TIME", formattedTime).apply();
            tvSelectedTime.setText("Scheduled Pill Time: " + formattedTime);

            Toast.makeText(this, "Pill reminder set for " + formattedTime, Toast.LENGTH_SHORT).show();

            // Send the scheduled time to the Raspberry Pi Flask server over Tailscale
            sendScheduleToRobot(formattedTime);
        }, hour, minute, true);

        timePickerDialog.show();
    }

    private void sendScheduleToRobot(String timeStr) {
        String robotIp = prefs.getString(KEY_ROBOT_IP, "");
        if (robotIp.isEmpty()) {
            runOnUiThread(() -> Toast.makeText(this, "Robot IP not configured", Toast.LENGTH_SHORT).show());
            return;
        }

        String url = "http://" + robotIp + ":5000/set_schedule";
        String jsonBody = "{\"time\": \"" + timeStr + "\"}";

        RequestBody body = RequestBody.create(jsonBody, MediaType.parse("application/json; charset=utf-8"));
        Request request = new Request.Builder().url(url).post(body).build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> Toast.makeText(Patient_Main.this, "Failed to send schedule to robot", Toast.LENGTH_SHORT).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                runOnUiThread(() -> Toast.makeText(Patient_Main.this, "Schedule synced with robot!", Toast.LENGTH_SHORT).show());
            }
        });
    }

    private void sendClearCommandToRobot() {
        String robotIp = prefs.getString(KEY_ROBOT_IP, "");
        if (robotIp.isEmpty()) {
            Toast.makeText(this, "Robot IP not configured", Toast.LENGTH_SHORT).show();
            return;
        }

        String url = "http://" + robotIp + ":5000/clear_display";
        RequestBody body = RequestBody.create("", MediaType.parse("application/json; charset=utf-8"));
        Request request = new Request.Builder().url(url).post(body).build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> Toast.makeText(Patient_Main.this, "Failed to reach robot", Toast.LENGTH_SHORT).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                runOnUiThread(() -> Toast.makeText(Patient_Main.this, "Alarm dismissed successfully!", Toast.LENGTH_SHORT).show());
            }
        });
    }
}