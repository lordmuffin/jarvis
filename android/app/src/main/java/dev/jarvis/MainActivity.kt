package dev.jarvis

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    Scaffold { padding ->
                        Column(
                            modifier = Modifier.padding(padding).padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Text("Jarvis", style = MaterialTheme.typography.headlineMedium)
                            Text(
                                "On-device intent classifier. Foreground service runs in the background.",
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            ManualTriggerButton()
                            // StatsScreen content lands in 1.9.
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ManualTriggerButton() {
    val ctx = LocalContext.current
    Button(onClick = {
        ctx.startActivity(Intent(ctx, ManualTriggerActivity::class.java))
    }) {
        Text("Open manual trigger")
    }
}
