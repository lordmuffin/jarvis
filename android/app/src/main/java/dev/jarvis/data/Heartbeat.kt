package dev.jarvis.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "heartbeats")
data class Heartbeat(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    /** Epoch millis when the WorkManager backstop fired (or service emitted). */
    @ColumnInfo(name = "recorded_at") val recordedAt: Long,
    /** True if the foreground service was confirmed alive at sample time. */
    @ColumnInfo(name = "service_alive") val serviceAlive: Boolean,
    /** Epoch millis of the last classify() call when sampled. Null at boot. */
    @ColumnInfo(name = "last_classify_at") val lastClassifyAt: Long? = null,
)
