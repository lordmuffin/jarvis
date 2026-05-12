package dev.jarvis.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query

@Dao
interface HeartbeatDao {

    @Insert
    suspend fun insert(heartbeat: Heartbeat)

    @Query("SELECT * FROM heartbeats WHERE recorded_at >= :sinceMillis ORDER BY recorded_at ASC")
    suspend fun since(sinceMillis: Long): List<Heartbeat>

    @Query("SELECT COUNT(*) FROM heartbeats WHERE recorded_at >= :sinceMillis")
    suspend fun countSince(sinceMillis: Long): Int
}
