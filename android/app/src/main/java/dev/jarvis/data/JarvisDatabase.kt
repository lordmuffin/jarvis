package dev.jarvis.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [Decision::class, Heartbeat::class],
    version = 1,
    exportSchema = true,
)
abstract class JarvisDatabase : RoomDatabase() {
    abstract fun decisionDao(): DecisionDao
    abstract fun heartbeatDao(): HeartbeatDao

    companion object {
        private const val DB_NAME = "jarvis.db"

        @Volatile
        private var INSTANCE: JarvisDatabase? = null

        fun get(context: Context): JarvisDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    JarvisDatabase::class.java,
                    DB_NAME,
                ).fallbackToDestructiveMigration().build().also { INSTANCE = it }
            }
    }
}
