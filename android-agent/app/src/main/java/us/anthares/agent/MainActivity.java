package us.anthares.agent;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int PICK_VIDEO = 501;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(28, 28, 28, 28);

        TextView description = new TextView(this);
        description.setText("Anthares — envio pelo aplicativo oficial Kwai\n" +
                "Este agente usa o Android real. O login e a confirmação de publicação " +
                "permanecem no aplicativo oficial do Kwai.");
        layout.addView(description);

        Button choose = new Button(this);
        choose.setText("Selecionar vídeo e abrir no Kwai");
        choose.setOnClickListener(v -> chooseVideo());
        layout.addView(choose);

        Button accessibility = new Button(this);
        accessibility.setText("Configurar acessibilidade do agente");
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

    private void chooseVideo() {
        Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        pick.setType("video/*");
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(pick, PICK_VIDEO);
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_VIDEO && result == RESULT_OK && data != null) {
            KwaiVideoHandoff.sharePicked(this, data.getData());
        }
    }

    private void inspectIncomingLink(Intent intent) {
        if (intent == null || !Intent.ACTION_VIEW.equals(intent.getAction())) return;
        Uri link = intent.getData();
        if (link == null || !"anthares-kwai".equals(link.getScheme())
                || !"send".equals(link.getHost())) return;
        new AlertDialog.Builder(this)
                .setTitle("Abrir vídeo no Kwai?")
                .setMessage("O Anthares baixará o vídeo do domínio anthares.us, " +
                        "verificará seu SHA-256 e o enviará ao aplicativo oficial do Kwai. " +
                        "Nenhum vídeo será publicado sem confirmação no Kwai.")
                .setNegativeButton("Cancelar", (dialog, which) -> {})
                .setPositiveButton("Continuar", (dialog, which) ->
                        KwaiVideoHandoff.shareFromApprovedLink(this, link))
                .show();
    }
}
