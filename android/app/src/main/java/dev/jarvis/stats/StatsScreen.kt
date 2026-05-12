package dev.jarvis.stats

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * Three KPI tiles for the Phase 1 acceptance gates:
 *
 *   1. 30-day rolling toast accept rate   — red < 60%, amber < 75%, green ≥ 75%
 *   2. 7-day toast volume + DOZE_KILLED   — red if heartbeats > 0 but toasts == 0
 *   3. Cold-start p50/p95 latency (24h)  — amber ≥ 400 ms, red ≥ 500 ms
 */
@Composable
fun StatsScreen(modifier: Modifier = Modifier) {
    val ctx = LocalContext.current
    val vm: StatsViewModel = viewModel(factory = StatsViewModel.factory(ctx))
    val state by vm.state.collectAsState()

    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Stats", style = MaterialTheme.typography.titleMedium)
            if (state.loading) {
                CircularProgressIndicator(modifier = Modifier.size(16.dp), strokeWidth = 2.dp)
            } else {
                TextButton(onClick = { vm.refresh() }) { Text("Refresh") }
            }
        }

        AcceptRateTile(state)
        ToastVolumeTile(state)
        LatencyTile(state)
    }
}

@Composable
private fun AcceptRateTile(state: StatsState) {
    val rate = state.acceptRate
    val pct = rate?.let { (it * 100).toInt() }
    val color = when {
        rate == null -> MaterialTheme.colorScheme.surfaceVariant
        rate < 0.60f -> Color(0xFFB00020)
        rate < 0.75f -> Color(0xFFF57C00)
        else -> Color(0xFF388E3C)
    }
    StatTile(
        label = "Accept rate (30d)",
        value = if (pct != null) "$pct%" else "—",
        subtitle = "${state.totalDecisions30d} decisions",
        indicatorColor = color,
    )
}

@Composable
private fun ToastVolumeTile(state: StatsState) {
    val dozeSuspected = state.heartbeatCount7d > 0 && state.toastCount7d == 0
    StatTile(
        label = "Toast volume (7d)",
        value = "${state.toastCount7d}",
        subtitle = if (dozeSuspected) "⚠ DOZE_KILLED?" else "${state.heartbeatCount7d} heartbeats",
        indicatorColor = if (dozeSuspected) Color(0xFFB00020) else MaterialTheme.colorScheme.primary,
    )
}

@Composable
private fun LatencyTile(state: StatsState) {
    val p95 = state.p95LatencyMs
    val color = when {
        p95 == null -> MaterialTheme.colorScheme.surfaceVariant
        p95 >= 500 -> Color(0xFFB00020)
        p95 >= 400 -> Color(0xFFF57C00)
        else -> Color(0xFF388E3C)
    }
    StatTile(
        label = "Inference latency (24h)",
        value = if (p95 != null) "p95: ${p95}ms" else "—",
        subtitle = state.p50LatencyMs?.let { "p50: ${it}ms" } ?: "no data",
        indicatorColor = color,
    )
}

@Composable
private fun StatTile(
    label: String,
    value: String,
    subtitle: String,
    indicatorColor: Color,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Row(
            modifier = Modifier
                .padding(12.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(
                modifier = Modifier.size(12.dp),
                shape = MaterialTheme.shapes.small,
                color = indicatorColor,
            ) {}
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    label,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    value,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
