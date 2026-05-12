package dev.jarvis.service.inference

/** WordPiece-style tokenizer interface. The real implementation reads
 *  tokenizer.json (huggingface tokenizers format) from app assets. */
interface Tokenizer {
    /** Maximum sequence length the tokenizer pads/truncates to. */
    val maxLength: Int

    /** Token id for the special [CLS] / [PAD] tokens. */
    val clsTokenId: Int
    val padTokenId: Int
    val sepTokenId: Int

    /**
     * Tokenize and convert to ids. The output arrays are exactly [maxLength] long —
     * padded with [padTokenId] and with a 0/1 attention mask.
     */
    fun encode(text: String): TokenizerOutput
}

data class TokenizerOutput(
    val inputIds: IntArray,
    val attentionMask: IntArray,
) {
    override fun equals(other: Any?): Boolean =
        other is TokenizerOutput &&
            inputIds.contentEquals(other.inputIds) &&
            attentionMask.contentEquals(other.attentionMask)

    override fun hashCode(): Int =
        31 * inputIds.contentHashCode() + attentionMask.contentHashCode()
}
