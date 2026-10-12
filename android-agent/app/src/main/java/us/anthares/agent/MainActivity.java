package us.anthares.agent;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(28, 28, 28, 28);

        TextView description = new TextView(this);
        description.setText("Anthares — executor automático do Kwai\n\n" +
                "O agente recebe o handoff remoto, baixa e valida o vídeo, abre o aplicativo oficial " +
                "do Kwai e conduz o fluxo de publicação. Não é necessário selecionar o vídeo manualmente.\n\n" +
                "A única configuração local necessária é manter a Acessibilidade do agente ativada.");
        layout.addView(description);

        Button accessibility = new Button(this);
        accessibility.setText("Ativar acessibilidade do agente (uma vez)");
        accessibility.setOnClickListener(v ->
                startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        layout.addView(accessibility);

        setContentView(layout);
        inspectIncomingLink(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        inspectIncomingLink(intent);
    }

    private void inspectIncomingLink(Intent intent) {
        if (intent == null || !Intent.ACTION_VIEW.equals(intent.getAction())) return;
        Uri link = intent.getData();
        if (link == null || !"anthares-kwai".equals(link.getScheme())
                || !"send".equals(link.getHost())) return;
        KwaiVideoHandoff.shareFromApprovedLink(this, link);
    }
}
