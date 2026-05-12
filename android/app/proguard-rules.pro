# Default Android optimize rules apply; per-rule keeps below.

# Room generated DAOs are accessed reflectively at runtime.
-keep class dev.jarvis.data.** { *; }

# kotlinx.serialization needs its serializer methods reachable.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keep,includedescriptorclasses class dev.jarvis.**$$serializer { *; }
-keepclassmembers class dev.jarvis.** {
    *** Companion;
}
-keepclasseswithmembers class dev.jarvis.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# LiteRT native bindings — keep the native bridges.
-keep class com.google.ai.edge.litert.** { *; }
