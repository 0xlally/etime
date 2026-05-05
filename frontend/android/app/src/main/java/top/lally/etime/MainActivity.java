package top.lally.etime;

import com.getcapacitor.BridgeActivity;
import android.os.Bundle;
import top.lally.etime.discipline.DisciplineModePlugin;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(DisciplineModePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
