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

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Έλεγχος αν ο χρήστης είναι ήδη συνδεδεμένος (Auto-Login)
        SharedPreferences pref = getSharedPreferences("UserPrefs", MODE_PRIVATE);
        boolean isLoggedIn = pref.getBoolean("IS_LOGGED_IN", false);
        if (isLoggedIn) {
            String accountType = pref.getString("ACCOUNT_TYPE", "Patient");
            Intent intent;
            if ("Caretaker".equalsIgnoreCase(accountType)) {
                intent = new Intent(this, CaretakerActivity.class);
            } else {
                intent = new Intent(this, PatientActivity.class);
            }
            intent.putExtra("ACCOUNT_TYPE", accountType);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            finish();
            return;
        }

        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });
    }

    // Συνδέεται με το android:onClick="onLoginClick" στο activity_main.xml
    public void onLoginClick(View v) {
        Intent intent = new Intent(this, New_Acc.class);
        intent.putExtra("ACTION_FLOW", "LOGIN");
        startActivity(intent);
    }

    // Συνδέεται με το android:onClick="onCreateAccClick" στο activity_main.xml
    public void onCreateAccClick(View v) {
        Intent intent = new Intent(this, New_Acc.class);
        intent.putExtra("ACTION_FLOW", "REGISTER");
        startActivity(intent);
    }
}