package dev.jarvis.service.inference

import com.google.common.truth.Truth.assertThat
import dev.jarvis.service.model.Accelerator
import dev.jarvis.service.model.EventSource
import dev.jarvis.service.model.IncomingEvent
import org.junit.Test

class StubClassifierTest {

    @Test
    fun stubIsDeterministicForSameText() {
        val s = StubClassifier()
        val a = s.classify(IncomingEvent(text = "hello world", source = EventSource.MANUAL_TEST))
        val b = s.classify(IncomingEvent(text = "hello world", source = EventSource.MANUAL_TEST))
        assertThat(a.intent).isEqualTo(b.intent)
    }

    @Test
    fun stubMarksAcceleratorAsAutoUnknown() {
        val s = StubClassifier()
        val d = s.classify(IncomingEvent(text = "anything", source = EventSource.MANUAL_TEST))
        assertThat(d.acceleratorUsed).isEqualTo(Accelerator.AUTO_UNKNOWN)
    }
}
