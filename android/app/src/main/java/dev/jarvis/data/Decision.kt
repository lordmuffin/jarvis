package dev.jarvis.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "decisions")
data class Decision(
    /** ULID assigned at event ingest. */
    @PrimaryKey @ColumnInfo(name = "event_id") val eventId: String,
    @ColumnInfo(name = "event_source") val eventSource: String,
    @ColumnInfo(name = "event_text") val eventText: String,
    @ColumnInfo(name = "predicted_intent") val predictedIntent: String,
    @ColumnInfo(name = "confidence") val confidence: Float,
    @ColumnInfo(name = "accelerator_used") val acceleratorUsed: String,
    @ColumnInfo(name = "inference_latency_ms") val inferenceLatencyMs: Long,
    @ColumnInfo(name = "user_action") val userAction: String? = null,
    @ColumnInfo(name = "created_at") val createdAt: Long,
    @ColumnInfo(name = "acted_at") val actedAt: Long? = null,
)
