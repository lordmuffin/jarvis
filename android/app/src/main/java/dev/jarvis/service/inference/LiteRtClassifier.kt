package dev.jarvis.service.inference

import android.content.Context
import android.util.Log
import com.google.ai.edge.litert.Accelerator
import com.google.ai.edge.litert.CompiledModel
import dev.jarvis.service.model.Accelerator as JarvisAccelerator
import dev.jarvis.service.model.IncomingEvent
import dev.jarvis.service.model.Intent
import dev.jarvis.service.model.IntentDecision
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import kotlin.math.exp

/**
 * LiteRT-backed MobileBERT intent classifier.
 *
 * Cold-start cost: model mmap (the asset is uncompressed via the
 * `noCompress.add("tflite")` setting in app/build.gradle.kts) + delegate
 * compilation. With `Accelerator.AUTO` on a Pixel 8 / Tensor G3 the runtime
 * should land on the EdgeTPU delegate; we log the selection on every cold
 * start so we notice if it silently falls back to CPU.
 *
 * Each [classify] call: tokenize → INT8 input copy → model.run → softmax →
 * argmax + confidence. Budgeted under 500 ms p95 (Phase 1 KPI gate).
 *
 * Note for API maintainers: the exact LiteRT Kotlin method names below
 * (`CompiledModel.create(Context, String, Options)`, `runInference`,
 * `getOutputBuffer`) match the 1.0.x SDK at the pinned version in
 * libs.versions.toml. If you bump that version and the API drifts, fix
 * here and the unit tests will guide you.
 */
class LiteRtClassifier private constructor(
    private val model: CompiledModel,
    private val tokenizer: Tokenizer,
    private val accelerator: JarvisAccelerator,
) : IntentClassifier {

    override fun classify(event: IncomingEvent): IntentDecision {
        val started = System.currentTimeMillis()
        val tok = tokenizer.encode(event.text)

        val inputIds = intArrayToInt32Buffer(tok.inputIds)
        val attentionMask = intArrayToInt32Buffer(tok.attentionMask)

        val outputBuf = ByteBuffer
            .allocateDirect(Intent.ORDER.size * Float.SIZE_BYTES)
            .order(ByteOrder.nativeOrder())

        // ---- LiteRT-version-sensitive block --------------------------------
        // The model has two int32 inputs (input_ids, attention_mask) and one
        // float32 output of shape [1, 7]. If this signature changes, only the
        // tensor binding below needs adjustment.
        model.run(
            listOf(inputIds, attentionMask),
            listOf(outputBuf),
        )
        // --------------------------------------------------------------------

        outputBuf.rewind()
        val logits = FloatArray(Intent.ORDER.size)
        for (i in logits.indices) logits[i] = outputBuf.float

        val probs = softmax(logits)
        val (argmax, confidence) = probs.bestPair()

        return IntentDecision(
            eventId = UUID.randomUUID().toString(),
            intent = Intent.fromOrdinal(argmax),
            confidence = confidence,
            acceleratorUsed = accelerator,
            latencyMs = System.currentTimeMillis() - started,
        )
    }

    override fun close() {
        try {
            model.close()
        } catch (e: Exception) {
            Log.w(TAG, "model.close() failed", e)
        }
    }

    companion object {
        private const val TAG = "LiteRtClassifier"
        const val MODEL_ASSET = "intent_router.tflite"
        const val TOKENIZER_ASSET = "tokenizer.json"

        /**
         * Try to load the LiteRT model + tokenizer from app assets.
         * Returns null and logs loudly if any asset is missing or the runtime
         * cannot compile the model on this device. Caller falls back to
         * [StubClassifier] in that case (and surfaces the setup state).
         */
        fun tryCreate(context: Context): LiteRtClassifier? {
            if (!context.assets.list("")?.contains(MODEL_ASSET).orFalse()) {
                Log.w(TAG, "asset $MODEL_ASSET not found — falling back to stub")
                return null
            }
            return try {
                val tokenizer = loadTokenizer(context)
                val options = CompiledModel.Options.builder()
                    .addAccelerator(Accelerator.AUTO)
                    .build()
                val model = CompiledModel.create(
                    context.assets,
                    MODEL_ASSET,
                    options,
                )
                val accelerator = mapAccelerator(model)
                Log.i(TAG, "LiteRT model loaded; accelerator=$accelerator")
                LiteRtClassifier(model, tokenizer, accelerator)
            } catch (e: Throwable) {
                Log.e(TAG, "LiteRT model load failed; falling back to stub", e)
                null
            }
        }

        private fun loadTokenizer(context: Context): Tokenizer {
            val raw = context.assets.open(TOKENIZER_ASSET).bufferedReader().use { it.readText() }
            return WordPieceTokenizer.fromTokenizerJson(raw)
        }

        private fun Boolean?.orFalse(): Boolean = this == true

        private fun mapAccelerator(model: CompiledModel): JarvisAccelerator {
            // LiteRT exposes the realized accelerator after compilation; this
            // string parsing is the LiteRT 1.0.x shape. The mapping is best-effort —
            // if AUTO landed on something unfamiliar we tag AUTO_UNKNOWN so it
            // shows up in the decision log rather than silently appearing as CPU.
            val name = runCatching { model.activeAccelerator?.name?.uppercase() }.getOrNull()
            return when (name) {
                "CPU" -> JarvisAccelerator.CPU
                "GPU" -> JarvisAccelerator.GPU
                "NPU", "EDGETPU" -> JarvisAccelerator.NPU
                else -> JarvisAccelerator.AUTO_UNKNOWN
            }
        }
    }
}

private fun intArrayToInt32Buffer(ids: IntArray): ByteBuffer {
    val buf = ByteBuffer.allocateDirect(ids.size * Int.SIZE_BYTES).order(ByteOrder.nativeOrder())
    for (id in ids) buf.putInt(id)
    buf.rewind()
    return buf
}

private fun softmax(logits: FloatArray): FloatArray {
    val maxLogit = logits.max()
    var sum = 0.0
    val exp = DoubleArray(logits.size) { i ->
        val e = exp((logits[i] - maxLogit).toDouble())
        sum += e
        e
    }
    return FloatArray(logits.size) { i -> (exp[i] / sum).toFloat() }
}

private fun FloatArray.bestPair(): Pair<Int, Float> {
    var idx = 0
    var best = this[0]
    for (i in 1 until size) {
        if (this[i] > best) {
            best = this[i]
            idx = i
        }
    }
    return idx to best
}
