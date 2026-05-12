package dev.jarvis.service.inference

import com.google.common.truth.Truth.assertThat
import org.junit.Test

/**
 * Tests use a tiny in-memory tokenizer.json. The full MobileBERT vocab has ~30k
 * tokens — we don't bundle it in tests; the on-device load is exercised by
 * instrumentation tests once 1.4 produces a real artifact.
 */
class WordPieceTokenizerTest {

    private val tinyVocab = """
        {
          "model": {
            "type": "WordPiece",
            "unk_token": "[UNK]",
            "max_input_chars_per_word": 100,
            "vocab": {
              "[PAD]": 0,
              "[UNK]": 1,
              "[CLS]": 2,
              "[SEP]": 3,
              "hello": 10,
              "world": 11,
              "##s": 12,
              "h": 13,
              "##e": 14,
              "##l": 15,
              "##o": 16,
              "!": 17,
              "schedule": 20,
              "meeting": 21
            }
          },
          "normalizer": {"lowercase": true}
        }
    """.trimIndent()

    @Test
    fun encodesKnownVocabExactly() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 16)
        val out = tok.encode("hello world")
        // [CLS] hello world [SEP] then PAD
        assertThat(out.inputIds[0]).isEqualTo(2)   // [CLS]
        assertThat(out.inputIds[1]).isEqualTo(10)  // hello
        assertThat(out.inputIds[2]).isEqualTo(11)  // world
        assertThat(out.inputIds[3]).isEqualTo(3)   // [SEP]
        // attention mask: 1 over real tokens, 0 over padding
        assertThat(out.attentionMask.take(4)).containsExactly(1, 1, 1, 1).inOrder()
        assertThat(out.attentionMask.drop(4).all { it == 0 }).isTrue()
        assertThat(out.inputIds.drop(4).all { it == 0 }).isTrue()  // PAD id
    }

    @Test
    fun lowercasesInput() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 16)
        val out = tok.encode("HELLO WORLD")
        assertThat(out.inputIds[1]).isEqualTo(10)
        assertThat(out.inputIds[2]).isEqualTo(11)
    }

    @Test
    fun splitsPunctuationAndMatchesGreedily() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 16)
        val out = tok.encode("hello!")
        // hello + ! (not "hello!")
        assertThat(out.inputIds[1]).isEqualTo(10)
        assertThat(out.inputIds[2]).isEqualTo(17)
        assertThat(out.inputIds[3]).isEqualTo(3)  // [SEP]
    }

    @Test
    fun fallsBackToWordPiecePieces() {
        // "hellos" should decompose to "hello" + "##s"
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 16)
        val out = tok.encode("hellos")
        assertThat(out.inputIds[1]).isEqualTo(10)  // hello
        assertThat(out.inputIds[2]).isEqualTo(12)  // ##s
    }

    @Test
    fun emitsUnkForUnseenWords() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 16)
        val out = tok.encode("hello quetzal world")
        // hello, [UNK], world
        assertThat(out.inputIds[1]).isEqualTo(10)
        assertThat(out.inputIds[2]).isEqualTo(1)
        assertThat(out.inputIds[3]).isEqualTo(11)
    }

    @Test
    fun paddingExactlyMaxLength() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 12)
        val out = tok.encode("hello world")
        assertThat(out.inputIds).hasLength(12)
        assertThat(out.attentionMask).hasLength(12)
    }

    @Test
    fun truncatesWhenOverMaxLength() {
        val tok = WordPieceTokenizer.fromTokenizerJson(tinyVocab, maxLength = 4)
        val out = tok.encode("hello world hello world")
        // 4 slots: [CLS] hello world [SEP]
        assertThat(out.inputIds[0]).isEqualTo(2)
        assertThat(out.inputIds[3]).isEqualTo(3)
        assertThat(out.attentionMask.all { it == 1 }).isTrue()
    }

    @Test
    fun rejectsNonWordPieceTokenizers() {
        val bpe = """{"model":{"type":"BPE","vocab":{},"unk_token":"[UNK]"}}"""
        try {
            WordPieceTokenizer.fromTokenizerJson(bpe)
            assert(false) { "expected IllegalArgumentException" }
        } catch (e: IllegalArgumentException) {
            assertThat(e.message).contains("WordPiece")
        }
    }
}
