package dev.jarvis.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DecisionDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(decision: Decision)

    @Query("""
        UPDATE decisions
           SET user_action = :userAction, acted_at = :actedAt
         WHERE event_id = :eventId
    """)
    suspend fun setUserAction(eventId: String, userAction: String, actedAt: Long): Int

    @Query("SELECT * FROM decisions WHERE event_id = :eventId LIMIT 1")
    suspend fun byEventId(eventId: String): Decision?

    @Query("SELECT * FROM decisions ORDER BY created_at DESC LIMIT :limit")
    fun recent(limit: Int = 200): Flow<List<Decision>>

    /** For the 30-day rolling accept-rate KPI. */
    @Query("""
        SELECT COUNT(*) FROM decisions
         WHERE user_action IN ('approve', 'edit')
           AND created_at >= :sinceMillis
    """)
    suspend fun approveCountSince(sinceMillis: Long): Int

    @Query("""
        SELECT COUNT(*) FROM decisions
         WHERE user_action IN ('approve', 'edit', 'dismiss')
           AND created_at >= :sinceMillis
    """)
    suspend fun acceptOrDismissCountSince(sinceMillis: Long): Int

    /** For the latency KPI. */
    @Query("""
        SELECT inference_latency_ms FROM decisions
         WHERE created_at >= :sinceMillis
         ORDER BY inference_latency_ms ASC
    """)
    suspend fun latenciesSince(sinceMillis: Long): List<Long>

    /** Per-day toast count for the 7-day volume KPI. */
    @Query("""
        SELECT COUNT(*) FROM decisions
         WHERE created_at >= :sinceMillis
           AND predicted_intent != 'dismiss'
    """)
    suspend fun toastCountSince(sinceMillis: Long): Int
}
