package dev.jarvis.stats

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import dev.jarvis.data.JarvisDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

data class StatsState(
    val acceptRate: Float? = null,
    val totalDecisions30d: Int = 0,
    val p50LatencyMs: Long? = null,
    val p95LatencyMs: Long? = null,
    val toastCount7d: Int = 0,
    val heartbeatCount7d: Int = 0,
    val loading: Boolean = true,
)

class StatsViewModel(private val db: JarvisDatabase) : ViewModel() {

    private val _state = MutableStateFlow(StatsState())
    val state: StateFlow<StatsState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch { loadStats() }
    }

    private suspend fun loadStats() = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        val thirtyDaysAgo = now - 30L * 24 * 3600 * 1000
        val sevenDaysAgo = now - 7L * 24 * 3600 * 1000
        val oneDayAgo = now - 24L * 3600 * 1000

        val approves = db.decisionDao().approveCountSince(thirtyDaysAgo)
        val total = db.decisionDao().acceptOrDismissCountSince(thirtyDaysAgo)
        val acceptRate = if (total > 0) approves.toFloat() / total else null

        val latencies = db.decisionDao().latenciesSince(oneDayAgo)
        val p50 = percentile(latencies, 0.50)
        val p95 = percentile(latencies, 0.95)

        val toastCount = db.decisionDao().toastCountSince(sevenDaysAgo)
        val heartbeatCount = db.heartbeatDao().countSince(sevenDaysAgo)

        _state.value = StatsState(
            acceptRate = acceptRate,
            totalDecisions30d = total,
            p50LatencyMs = p50,
            p95LatencyMs = p95,
            toastCount7d = toastCount,
            heartbeatCount7d = heartbeatCount,
            loading = false,
        )
    }

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory = viewModelFactory {
            initializer { StatsViewModel(JarvisDatabase.get(context.applicationContext)) }
        }

        private fun percentile(sorted: List<Long>, pct: Double): Long? {
            if (sorted.isEmpty()) return null
            val idx = (pct * (sorted.size - 1)).roundToInt().coerceIn(0, sorted.lastIndex)
            return sorted[idx]
        }
    }
}
