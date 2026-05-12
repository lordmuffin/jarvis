package dev.jarvis.service.inference

import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * BERT-style WordPiece tokenizer that reads its vocab from the `tokenizer.json`
 * artifact produced by the training pipeline (huggingface tokenizers format).
 *
 * This is intentionally minimal: lower-case + basic whitespace/punctuation
 * splitting, greedy longest-match WordPiece. It is **not** a general-purpose
 * tokenizer — it matches what `training/jarvis_training/train/train.py` writes
 * out for MobileBERT. CI guards the tokenizer hash (.tokenizer.sha256) so
 * drift between training-side and on-device tokenization fails the build.
 */
class WordPieceTokenizer private constructor(
    private val vocab: Map<String, Int>,
    private val unkTokenId: Int,
    override val maxLength: Int,
    override val clsTokenId: Int,
    override val padTokenId: Int,
    override val sepTokenId: Int,
    private val maxInputCharsPerWord: Int,
    private val doLowerCase: Boolean,
) : Tokenizer {

    override fun encode(text: String): TokenizerOutput {
        val tokens = mutableListOf<Int>()
        tokens.add(clsTokenId)
        for (word in basicTokenize(text)) {
            tokens.addAll(wordpiece(word))
            if (tokens.size >= maxLength - 1) break
        }
        if (tokens.size >= maxLength) {
            // Truncate, keep room for [SEP].
            while (tokens.size > maxLength - 1) tokens.removeAt(tokens.size - 1)
        }
        tokens.add(sepTokenId)

        val ids = IntArray(maxLength) { padTokenId }
        val mask = IntArray(maxLength)
        for (i in tokens.indices) {
            ids[i] = tokens[i]
            mask[i] = 1
        }
        return TokenizerOutput(inputIds = ids, attentionMask = mask)
    }

    private fun basicTokenize(text: String): List<String> {
        val normalized = if (doLowerCase) text.lowercase() else text
        val out = mutableListOf<String>()
        val sb = StringBuilder()
        for (ch in normalized) {
            when {
                ch.isWhitespace() -> {
                    if (sb.isNotEmpty()) {
                        out.add(sb.toString()); sb.clear()
                    }
                }
                ch.isPunctuation() -> {
                    if (sb.isNotEmpty()) {
                        out.add(sb.toString()); sb.clear()
                    }
                    out.add(ch.toString())
                }
                else -> sb.append(ch)
            }
        }
        if (sb.isNotEmpty()) out.add(sb.toString())
        return out
    }

    private fun Char.isPunctuation(): Boolean =
        // BERT's IsPunctuation: ASCII punctuation + Unicode P* categories.
        (this in '!'..'/') ||
            (this in ':'..'@') ||
            (this in '['..'`') ||
            (this in '{'..'~') ||
            (Character.getType(this).let { t ->
                t == Character.CONNECTOR_PUNCTUATION.toInt() ||
                    t == Character.DASH_PUNCTUATION.toInt() ||
                    t == Character.START_PUNCTUATION.toInt() ||
                    t == Character.END_PUNCTUATION.toInt() ||
                    t == Character.INITIAL_QUOTE_PUNCTUATION.toInt() ||
                    t == Character.FINAL_QUOTE_PUNCTUATION.toInt() ||
                    t == Character.OTHER_PUNCTUATION.toInt()
            })

    private fun wordpiece(word: String): List<Int> {
        if (word.length > maxInputCharsPerWord) return listOf(unkTokenId)
        val subTokens = mutableListOf<Int>()
        var start = 0
        while (start < word.length) {
            var end = word.length
            var found = -1
            while (end > start) {
                val sub = (if (start == 0) word.substring(start, end) else "##" + word.substring(start, end))
                val id = vocab[sub]
                if (id != null) {
                    found = id
                    break
                }
                end--
            }
            if (found == -1) return listOf(unkTokenId)
            subTokens.add(found)
            start = end
        }
        return subTokens
    }

    companion object {
        const val DEFAULT_MAX_LENGTH = 128

        @OptIn(ExperimentalSerializationApi::class)
        private val json = Json { ignoreUnknownKeys = true; isLenient = true }

        /**
         * Load from a tokenizer.json file (huggingface tokenizers format).
         *
         * @param tokenizerJson the raw JSON contents
         * @param maxLength override the max sequence length (default: 128, matches
         *   training/jarvis_training/train/train.py)
         */
        fun fromTokenizerJson(
            tokenizerJson: String,
            maxLength: Int = DEFAULT_MAX_LENGTH,
        ): WordPieceTokenizer {
            val root: JsonObject = json.parseToJsonElement(tokenizerJson).jsonObject
            val model: JsonObject = (root["model"] ?: error("tokenizer.json missing 'model'"))
                .jsonObject
            val type = model["type"]?.jsonPrimitive?.contentOrNull
            require(type == "WordPiece") {
                "Only WordPiece tokenizer is supported in Phase 1 (got type=$type)"
            }
            val unkToken = model["unk_token"]?.jsonPrimitive?.contentOrNull ?: "[UNK]"
            val maxChars = model["max_input_chars_per_word"]?.jsonPrimitive?.intOrNull ?: 100

            val vocab: Map<String, Int> = (model["vocab"]?.jsonObject
                ?: error("tokenizer.json missing 'model.vocab'"))
                .entries.associate { (k, v) ->
                    k to (v.jsonPrimitive.intOrNull
                        ?: error("vocab value for $k is not an integer"))
                }

            val unkId = vocab[unkToken] ?: error("unk_token $unkToken missing from vocab")
            val padId = vocab["[PAD]"] ?: error("[PAD] missing from vocab")
            val clsId = vocab["[CLS]"] ?: error("[CLS] missing from vocab")
            val sepId = vocab["[SEP]"] ?: error("[SEP] missing from vocab")

            val doLowerCase = readNestedBool(root, listOf("normalizer", "lowercase")) ?: true
            return WordPieceTokenizer(
                vocab = vocab,
                unkTokenId = unkId,
                maxLength = maxLength,
                clsTokenId = clsId,
                padTokenId = padId,
                sepTokenId = sepId,
                maxInputCharsPerWord = maxChars,
                doLowerCase = doLowerCase,
            )
        }

        private fun readNestedBool(root: JsonObject, path: List<String>): Boolean? {
            var node: JsonElement? = root
            for (key in path) {
                node = (node as? JsonObject)?.get(key) ?: return null
            }
            return (node as? JsonPrimitive)?.content?.toBooleanStrictOrNull()
        }
    }
}

@Serializable
private class TokenizerJsonShape  // placeholder, real parsing is dynamic above
