package dev.jarvis.service.inference

/**
 * Process-wide handle to the classifier instance owned by [IntentRouterService].
 *
 * The service sets this after cold-start model load; clients (ManualTriggerActivity,
 * SmokeTestReceiver, the notification-listener pipeline) read it for synchronous
 * `classify()` calls. Phase 1 is single-process so the simple singleton is enough;
 * if a remote process is ever needed we'd swap to a binder.
 */
object ClassifierHolder {
    @Volatile
    private var current: IntentClassifier? = null

    fun set(classifier: IntentClassifier?) {
        current = classifier
    }

    fun get(): IntentClassifier? = current
}
