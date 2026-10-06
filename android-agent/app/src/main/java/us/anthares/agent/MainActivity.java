package us.anthares.agent;
import android.app.Activity; import android.content.Intent; import android.os.Bundle; import android.provider.Settings; import android.widget.TextView;
public class MainActivity extends Activity { @Override public void onCreate(Bundle b){ super.onCreate(b); TextView v=new TextView(this); v.setText("Anthares Android Agent\nEnable Accessibility Service to control the official Kwai app."); v.setPadding(32,32,32,32); v.setOnClickListener(x->startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))); setContentView(v); } }
