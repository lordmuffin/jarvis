package dev.jarvis.data

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class DecisionDaoTest {

    private lateinit var db: JarvisDatabase
    private val dao get() = db.decisionDao()

    @Before fun setup() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            JarvisDatabase::class.java,
        ).allowMainThreadQueries().build()
    }

    @After fun teardown() { db.close() }

    private fun seed(intent: String, userAction: String?, latencyMs: Long, ageMs: Long): Decision {
        val now = System.currentTimeMillis()
        return Decision(
            eventId = "evt-$intent-$ageMs",
            eventSource = "manual_test",
            eventText = "x",
            predictedIntent = intent,
            confidence = 0.9f,
            acceleratorUsed = "NPU",
            inferenceLatencyMs = latencyMs,
            userAction = userAction,
            createdAt = now - ageMs,
            actedAt = if (userAction != null) now - ageMs + 1000 else null,
        )
    }

    @Test fun insertAndReadBackByEventId() = runBlocking {
        val d = seed("draft.email", "approve", 50, 0)
        dao.insert(d)
        assertThat(dao.byEventId(d.eventId)).isEqualTo(d)
    }

    @Test fun setUserActionUpdatesRow() = runBlocking {
        val d = seed("draft.email", null, 50, 0)
        dao.insert(d)
        val rows = dao.setUserAction(d.eventId, "approve", System.currentTimeMillis())
        assertThat(rows).isEqualTo(1)
        assertThat(dao.byEventId(d.eventId)?.userAction).isEqualTo("approve")
    }

    @Test fun acceptRateCounters() = runBlocking {
        val nowAgo = 0L
        dao.insert(seed("draft.email", "approve", 50, nowAgo))
        dao.insert(seed("dismiss", "dismiss", 50, nowAgo))
        dao.insert(seed("draft.email", "edit", 50, nowAgo))
        dao.insert(seed("draft.email", "dismiss", 50, nowAgo))
        val since = 0L  // all
        assertThat(dao.approveCountSince(since)).isEqualTo(2)  // approve + edit
        assertThat(dao.acceptOrDismissCountSince(since)).isEqualTo(4)
    }

    @Test fun toastCountExcludesDismissIntent() = runBlocking {
        dao.insert(seed("draft.email", "approve", 50, 0))
        dao.insert(seed("dismiss", null, 50, 0))
        dao.insert(seed("schedule.event", null, 50, 0))
        // toast count counts everything *not* labeled dismiss
        assertThat(dao.toastCountSince(0L)).isEqualTo(2)
    }

    @Test fun latencyOrderedAscending() = runBlocking {
        listOf(100L, 30L, 200L, 50L).forEach {
            dao.insert(seed("draft.email", "approve", it, 0L))
        }
        assertThat(dao.latenciesSince(0L)).containsExactly(30L, 50L, 100L, 200L).inOrder()
    }
}
