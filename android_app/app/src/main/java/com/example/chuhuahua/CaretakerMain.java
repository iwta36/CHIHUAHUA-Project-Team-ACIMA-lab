package com.example.chuhuahua;

import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;

public class CaretakerMain extends AppCompatActivity {

    private EditText etRobotIp;
    private Button btnConnectCamera;
    private RecyclerView rvChatFeed;
    private ChatAdapter chatAdapter;
    private List<ChatMessage> chatMessageList;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_caretaker_main);

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        // Initialize UI components
        etRobotIp = findViewById(R.id.etRobotIp);
        btnConnectCamera = findViewById(R.id.btnConnectCamera);
        rvChatFeed = findViewById(R.id.rvChatFeed);

        // Pre-fill Robot IP if previously saved
        SharedPreferences prefs = getSharedPreferences("CaretakerPrefs", MODE_PRIVATE);
        String savedRobotIp = prefs.getString("ROBOT_IP", "");
        if (etRobotIp != null && !savedRobotIp.isEmpty()) {
            etRobotIp.setText(savedRobotIp);
        }

        // Initialize Chat RecyclerView pipeline
        chatMessageList = new ArrayList<>();
        chatAdapter = new ChatAdapter(chatMessageList);
        rvChatFeed.setLayoutManager(new LinearLayoutManager(this));
        rvChatFeed.setAdapter(chatAdapter);

        // Configure connection trigger using the standard View.OnClickListener block pattern
        if (btnConnectCamera != null) {
            btnConnectCamera.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    String ip = etRobotIp != null ? etRobotIp.getText().toString().trim() : "";

                    if (ip.isEmpty()) {
                        Toast.makeText(CaretakerMain.this, "Please enter a valid IP address", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    String streamUrl = "http://" + ip + ":5000/";
                    try {
                        Uri uri = Uri.parse(streamUrl);
                        Intent browserIntent = new Intent(Intent.ACTION_VIEW, uri);
                        startActivity(browserIntent);
                    } catch (Exception e) {
                        e.printStackTrace();
                        Toast.makeText(CaretakerMain.this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }
            });
        }
    }
}
