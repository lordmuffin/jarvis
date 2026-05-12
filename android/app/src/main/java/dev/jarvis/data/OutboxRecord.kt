package dev.jarvis.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Schema of one line in `outbox/jarvis-decisions/YYYY-MM-DD.jsonl`. */
@Serializable
data class OutboxDecisionRecord(
    @SerialName("event_id") val eventId: String,
    @SerialName("event_source") val eventSource: String,
    @SerialName("event_text") val eventText: String,
    @SerialName("predicted_intent") val predictedIntent: String,
    val confidence: Float,
    @SerialName("accelerator_used") val acceleratorUsed: String,
    @SerialName("inference_latency_ms") val inferenceLatencyMs: Long,
    @SerialName("user_action") val userAction: String? = null,
    @SerialName("created_at_ms") val createdAtMs: Long,
    @SerialName("acted_at_ms") val actedAtMs: Long? = null,
    /** Schema version for downstream consumers on the homelab. */
    @SerialName("intent_schema_version") val intentSchemaVersion: String,
)

fun Decision.toOutboxRecord(schemaVersion: String): OutboxDecisionRecord =
    OutboxDecisionRecord(
        eventId = eventId,
        eventSource = eventSource,
        eventText = eventText,
        predictedIntent = predictedIntent,
        confidence = confidence,
        acceleratorUsed = acceleratorUsed,
        inferenceLatencyMs = inferenceLatencyMs,
        userAction = userAction,
        createdAtMs = createdAt,
        actedAtMs = actedAt,
        intentSchemaVersion = schemaVersion,
    )
