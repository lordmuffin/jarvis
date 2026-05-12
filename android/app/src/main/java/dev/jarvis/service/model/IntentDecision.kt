package dev.jarvis.service.model

import kotlinx.serialization.Serializable

enum class Accelerator { CPU, GPU, NPU, AUTO_UNKNOWN }

@Serializable
data class IntentDecision(
    /** ULID assigned on event ingest. */
    val eventId: String,
    val intent: Intent,
    val confidence: Float,
    /** Which LiteRT delegate ran the inference. AUTO_UNKNOWN means the runtime
     *  didn't tell us — surface this in logs so we notice. */
    val acceleratorUsed: Accelerator,
    /** Wall-clock time spent inside `classify()`, including tokenize + infer. */
    val latencyMs: Long,
)
