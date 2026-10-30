package com.example.chuhuahua;

import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

import java.io.IOException;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class CaretakerActivity extends AppCompatActivity {

    private LinearLayout layoutCaretakerSetup, layoutCaretakerDashboard;
    private EditText etPatientPhone, etRobotIp;
    private Button btnSaveCaretakerSetup, btnVideoCall;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_caretaker);

        layoutCaretakerSetup = findViewById(R.id.layoutCaretakerSetup);
        layoutCaretakerDashboard = findViewById(R.id.layoutCaretakerDashboard);
        etPatientPhone = findViewById(R.id.etPatientPhone);
        etRobotIp = findViewById(R.id.etRobotIp);
        btnSaveCaretakerSetup = findViewById(R.id.btnSaveCaretakerSetup);
        btnVideoCall = findViewById(R.id.btnVideoCall);

        prefs = getSharedPreferences("CaretakerPrefs", MODE_PRIVATE);

        String savedRobotIp = prefs.getString("ROBOT_IP", "");
        if (!savedRobotIp.isEmpty()) {
            Intent intent = new Intent(this, CaretakerMain.class);
            startActivity(intent);
            finish();
            return;
        }

        layoutCaretakerSetup.setVisibility(View.VISIBLE);
        if (layoutCaretakerDashboard != null) {
            layoutCaretakerDashboard.setVisibility(View.GONE);
        }

        btnSaveCaretakerSetup.setOnClickListener(v -> saveConfigLocally());
        if (btnVideoCall != null) {
            btnVideoCall.setOnClickListener(v -> initiateVideoCallToRobot());
        }
    }

    private void saveConfigLocally() {
        String patientPhone = etPatientPhone.getText().toString().trim();
        String robotIp = etRobotIp.getText().toString().trim();

        if (patientPhone.isEmpty() || robotIp.isEmpty()) {
            Toast.makeText(this, "Please enter both fields", Toast.LENGTH_SHORT).show();
            return;
        }

        // 1. Αποθήκευση τοπικά
        prefs.edit()
                .putString("PATIENT_PHONE", patientPhone)
                .putString("ROBOT_IP", robotIp)
                .apply();

        // 2. Αποστολή του τηλεφώνου στο Raspberry Pi μέσω OkHttp
        String url = "http://" + robotIp + ":5000/set_caretaker_phone";
        String jsonBody = "{\"phone\": \"" + patientPhone + "\"}";

        OkHttpClient client = new OkHttpClient();
        RequestBody body = RequestBody.create(jsonBody, MediaType.parse("application/json; charset=utf-8"));
        Request request = new Request.Builder().url(url).post(body).build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                runOnUiThread(() -> Toast.makeText(CaretakerActivity.this, "Failed to sync phone with robot", Toast.LENGTH_SHORT).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                runOnUiThread(() -> {
                    Toast.makeText(CaretakerActivity.this, "Caretaker phone & IP linked successfully!", Toast.LENGTH_SHORT).show();
                    Intent intent = new Intent(CaretakerActivity.this, CaretakerMain.class);
                    startActivity(intent);
                    finish();
                });
            }
        });
    }

    private void initiateVideoCallToRobot() {
        // Fallback to reading live text if field is visible, otherwise use saved preference
        String ip = "";
        if (etRobotIp != null && layoutCaretakerSetup.getVisibility() == View.VISIBLE) {
            ip = etRobotIp.getText().toString().trim();
        }

        if (ip.isEmpty()) {
            ip = prefs.getString("ROBOT_IP", "");
        }

        if (ip.isEmpty()) {
            Toast.makeText(this, "Please enter a valid IP address", Toast.LENGTH_SHORT).show();
            return;
        }

        String streamUrl = "http://" + ip + ":5000/";
        try {
            Uri uri = Uri.parse(streamUrl);
            Intent browserIntent = new Intent(Intent.ACTION_VIEW, uri);
            startActivity(browserIntent);
        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }
}
