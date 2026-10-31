package com.example.chuhuahua;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

public class New_Acc extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_new_acc);

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });
    }

    public void CaretakerButton(View v) {
        handleRoleSelection("Caretaker");
    }

    public void PatientButton(View v) {
        handleRoleSelection("Patient");
    }

    private void handleRoleSelection(String role) {
        SharedPreferences pref = getSharedPreferences("UserPrefs", MODE_PRIVATE);
        pref.edit()
            .putBoolean("IS_LOGGED_IN", true)
            .putString("ACCOUNT_TYPE", role)
            .apply();

        Intent intent;
        if ("Caretaker".equalsIgnoreCase(role)) {
            intent = new Intent(this, RegAct.class);
        } else {
            intent = new Intent(this, RegAct.class);
        }
        
        intent.putExtra("ACCOUNT_TYPE", role);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
    }
}
