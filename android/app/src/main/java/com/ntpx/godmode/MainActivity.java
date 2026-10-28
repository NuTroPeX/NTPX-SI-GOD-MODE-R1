package com.ntpx.godmode;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;
import android.net.Uri;
public class MainActivity extends Activity {
  @Override public void onCreate(Bundle b){super.onCreate(b);
    LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);
    EditText url=new EditText(this);url.setSingleLine(true);url.setHint("Backend URL (HTTPS or local HTTP)");url.setText("http://127.0.0.1:8765");
    Button go=new Button(this);go.setText("Connect to backend");
    WebView web=new WebView(this);web.getSettings().setJavaScriptEnabled(true);web.setWebViewClient(new WebViewClient());
    l.addView(url);l.addView(go);l.addView(web,new LinearLayout.LayoutParams(-1,0,1));setContentView(l);
    go.setOnClickListener(v->{String s=url.getText().toString().trim();Uri u=Uri.parse(s);String host=u.getHost();boolean local="127.0.0.1".equals(host)||"localhost".equals(host);if(!"https".equals(u.getScheme())&&! (local&&"http".equals(u.getScheme()))){Toast.makeText(this,"Use HTTPS or localhost",Toast.LENGTH_LONG).show();return;}web.loadUrl(s);});
  }
}
