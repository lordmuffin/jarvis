package dev.jarvis

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.jarvis.service.IntentRouterClient
import dev.jarvis.service.model.EventSource
import dev.jarvis.service.model.IncomingEvent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** Paste any text and run it through the classifier. Used for hand-testing the
 *  pipeline without depending on real email or calendar events. */
class ManualTriggerActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    ManualTriggerForm()
                }
            }
        }
    }
}

@androidx.compose.runtime.Composable
private fun ManualTriggerForm() {
    var text by remember { mutableStateOf("") }
    var lastResult by remember { mutableStateOf<String?>(null) }
    val scope = remember { CoroutineScope(Dispatchers.Main) }
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val client = remember { IntentRouterClient(ctx) }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Manual trigger", style = MaterialTheme.typography.headlineSmall)
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            label = { Text("Event text") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = {
            scope.launch {
                val decision = client.classify(
                    IncomingEvent(text = text, source = EventSource.MANUAL_TEST),
                )
                lastResult = "${decision.intent} · ${"%.2f".format(decision.confidence)} · " +
                    "${decision.acceleratorUsed} · ${decision.latencyMs}ms"
            }
        }, enabled = text.isNotBlank()) {
            Text("Classify")
        }
        lastResult?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
    }
}
