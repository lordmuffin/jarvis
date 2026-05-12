package dev.jarvis.ui.edit

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import dev.jarvis.data.JarvisDatabase
import dev.jarvis.data.UserAction
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Transparent-ish activity that shows a Compose bottom sheet for editing a
 * draft before it is sent. Launched by [ToastActionReceiver] when the user
 * taps the Edit action on a HUN.
 *
 * On Send: records user_action = 'edit' in Room, then finishes.
 * On Cancel: finishes without writing anything (the notification was already
 * dismissed by [ToastActionReceiver], so the decision remains unresolved —
 * it will be picked up by the timeout alarm if the user never re-opens).
 */
class EditActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val eventId = intent.getStringExtra(EXTRA_EVENT_ID) ?: run {
            Log.w(TAG, "launched without $EXTRA_EVENT_ID — finishing")
            finish()
            return
        }
        val draftPayload = intent.getStringExtra(EXTRA_DRAFT_PAYLOAD) ?: ""

        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    EditDraftSheet(
                        eventId = eventId,
                        initialText = draftPayload,
                        onSend = { finish() },
                        onCancel = { finish() },
                    )
                }
            }
        }
    }

    companion object {
        const val EXTRA_EVENT_ID = "dev.jarvis.extra.EVENT_ID"
        const val EXTRA_DRAFT_PAYLOAD = "dev.jarvis.extra.DRAFT_PAYLOAD"
        private const val TAG = "EditActivity"
    }
}

@Composable
private fun EditDraftSheet(
    eventId: String,
    initialText: String,
    onSend: () -> Unit,
    onCancel: () -> Unit,
) {
    var text by remember { mutableStateOf(initialText) }
    var sending by remember { mutableStateOf(false) }
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Edit draft", style = MaterialTheme.typography.titleMedium)

        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            label = { Text("Draft") },
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            maxLines = 30,
            enabled = !sending,
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.End),
        ) {
            OutlinedButton(onClick = onCancel, enabled = !sending) {
                Text("Cancel")
            }
            Button(
                onClick = {
                    sending = true
                    scope.launch {
                        withContext(Dispatchers.IO) {
                            JarvisDatabase.get(ctx)
                                .decisionDao()
                                .setUserAction(
                                    eventId,
                                    UserAction.EDIT.wire,
                                    System.currentTimeMillis(),
                                )
                        }
                        onSend()
                    }
                },
                enabled = text.isNotBlank() && !sending,
            ) {
                Text("Send")
            }
        }
    }
}
